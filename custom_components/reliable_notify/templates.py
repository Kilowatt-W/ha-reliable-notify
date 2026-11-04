"""Reusable notification template definitions and validation."""
from __future__ import annotations

import re

TEMPLATE_NAME=re.compile(r"^[a-z][a-z0-9_]{0,63}$")
MAX_TEXT=8192


def validate_templates(mapping):
    """Only administrator-managed template definitions are accepted."""
    if not isinstance(mapping,dict) or len(mapping)>150:
        raise ValueError("templates must be a mapping of at most 150 definitions")
    validated={}
    for name,spec in mapping.items():
        if not isinstance(name,str) or not TEMPLATE_NAME.fullmatch(name):
            raise ValueError("invalid template name")
        if not isinstance(spec,dict) or set(spec)-{
            "title","message","priority","recipients","message_type","archive","archive_days"
        }:
            raise ValueError("unsupported template fields")
        message=spec.get("message")
        if not isinstance(message,str) or not message or len(message)>MAX_TEXT:
            raise ValueError("each template requires a message (max 8192 characters)")
        title=spec.get("title","")
        if not isinstance(title,str) or len(title)>256:
            raise ValueError("invalid title")
        if spec.get("priority","info") not in ("info","warning","critical"):
            raise ValueError("invalid priority")
        if "recipients" in spec:
            value=spec["recipients"]
            if isinstance(value,str):value=[value]
            if not isinstance(value,list) or not value or not all(
                isinstance(x,str) and TEMPLATE_NAME.fullmatch(x) for x in value
            ):
                raise ValueError("invalid recipients")
        if spec.get("archive","keep") not in ("keep","delete_after_send"):
            raise ValueError("invalid archive")
        if "archive_days" in spec and (type(spec["archive_days"]) is not int
            or not 0<=spec["archive_days"]<=365):
            raise ValueError("invalid archive_days")
        validated[name]=dict(spec)
    return validated


def validate_parameters(params):
    if not isinstance(params,dict) or len(params)>50:
        raise ValueError("template variables must be a small mapping")
    for key,value in params.items():
        if not isinstance(key,str) or not TEMPLATE_NAME.fullmatch(key):
            raise ValueError("invalid template variable")
        if not isinstance(value,(str,int,float,bool,type(None))) or len(str(value))>2048:
            raise ValueError("invalid template variable value")
    return params
