"""Read-only proposal engine for Home Assistant notify automation migration.

No automation files are ever modified. Proposals are intentionally conservative:
only unambiguous routes and static destination selectors are considered safe.
"""
from __future__ import annotations

from copy import deepcopy
import re

TEMPLATE = re.compile(r"\{[{%]|[%}]\}")


def route_targets(routes):
    """Canonicalize configured destinations for static source lookup."""
    index={}
    for name,spec in routes.get("recipients",{}).items():
        action=spec.get("action","notify.send_message")
        data=spec.get("data",{})
        key=None
        if action=="notify.send_message":
            target=spec.get("target_entity")
            if target:
                key=(action,str(target))
        elif action.startswith("telegram_bot."):
            selector=next((k for k in ("chat_id","entity_id","config_entry_id")
                           if k in data),None)
            if selector and not isinstance(data[selector],(dict,list)):
                key=(action,str(data[selector]))
        elif action.startswith("notify.") or action.startswith("rest_command."):
            key=(action,"")
        if key:
            index.setdefault(key,[]).append(name)
    return index


def inspect_action(node,index):
    """Return safe migration metadata or reason it requires manual review."""
    action=node.get("action",node.get("service"))
    if not isinstance(action,str) or TEMPLATE.search(action):
        return None
    if not (action.startswith("notify.") or action.startswith("telegram_bot.")
            or action.startswith("smtp.")):
        return None
    if action.startswith("notify.reliable_"):
        return None
    if "service_template" in node or "data_template" in node:
        return {"status":"manual","reason":"Templated service/data action", "source":action}
    body=node.get("data",{})
    if not isinstance(body,dict):
        return {"status":"manual","reason":"Non-object data", "source":action}
    target=node.get("target",{})
    if target is None:
        target={}
    if not isinstance(target,dict) or set(target)-{"entity_id"}:
        return {"status":"manual","reason":"Non-static or complex target", "source":action}
    keys=set(node)-{"action","service","data","target","alias","continue_on_error","enabled"}
    if keys:
        return {"status":"manual","reason":"Advanced action fields", "source":action}
    destination=""
    if action=="notify.send_message":
        if "entity_id" in body:
            return {"status":"manual","reason":"notify entity in data instead of target","source":action}
        destination=target.get("entity_id","")
        if isinstance(destination,list) and len(destination)==1:
            destination=destination[0]
    elif action.startswith("telegram_bot."):
        found=[key for key in ("chat_id","entity_id","config_entry_id") if key in body]
        if len(found)!=1:
            return {"status":"manual","reason":"Telegram destination is ambiguous","source":action}
        destination=body[found[0]]
        if any(key in target for key in ("entity_id",)):
            return {"status":"manual","reason":"Unexpected separate Telegram target","source":action}
    elif action.startswith("notify.") and action!="notify.notify":
        if target:
            return {"status":"manual","reason":"Legacy notify action has extra target","source":action}
    else:
        return {"status":"manual","reason":"No unique static notify destination","source":action}
    if not isinstance(destination,(str,int)) or TEMPLATE.search(str(destination)):
        return {"status":"manual","reason":"Dynamic or multi-recipient destination","source":action}
    matches=index.get((action,str(destination)),[])
    if len(matches)!=1:
        return {"status":"manual","reason":("No configured matching route" if not matches
                                             else "Multiple routes match destination"),"source":action}
    route=matches[0]
    extra=set(body)-{"title","message"}
    if action.startswith("telegram_bot."):
        extra-={"chat_id","entity_id","config_entry_id"}
    if extra:
        return {"status":"manual","reason":"Transport-specific data must be reviewed",
                "source":action,"suggested_route":route}
    if "message" not in body:
        return {"status":"manual","reason":"Missing message", "source":action}
    replacement={
        "action":"notify.reliable_"+route,
        "data":{"message":deepcopy(body["message"])}
    }
    if "title" in body:
        replacement["data"]["title"]=deepcopy(body["title"])
    if "alias" in node:
        replacement["alias"]=node["alias"]
    if "continue_on_error" in node:
        replacement["continue_on_error"]=node["continue_on_error"]
    if "enabled" in node:
        replacement["enabled"]=node["enabled"]
    return {"status":"proposed","source":action,"route":route,
            "replacement":replacement,"reason":"Unambiguous static destination"}


def analyze(root,routes,limit=300):
    """Inspect nested sequences/choose/repeat/parallel without mutating YAML."""
    if not isinstance(root,(dict,list)) or not 1<=limit<=2000:
        raise ValueError("invalid automation document or suggestion limit")
    index=route_targets(routes)
    results=[]
    visited=set()
    def walk(obj,path,automation="",depth=0):
        if len(results)>=limit or depth>32:
            return
        if isinstance(obj,(dict,list)):
            identity=id(obj)
            if identity in visited:
                return
            visited.add(identity)
        if isinstance(obj,list):
            for idx,item in enumerate(obj):
                walk(item,f"{path}[{idx}]",automation,depth+1)
        elif isinstance(obj,dict):
            label=str(obj.get("alias") or obj.get("id") or automation)
            inspection=inspect_action(obj,index)
            if inspection:
                results.append({"path":path,"automation":label,**inspection})
            for key,value in obj.items():
                if isinstance(value,(dict,list)):
                    walk(value,f"{path}.{key}",label,depth+1)
    walk(root,"root")
    return results
