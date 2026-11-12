PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "intent": {"type": "string"},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "section_title": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "description": {"type": "string"},
                                "language": {"type": "string"},
                                "code_block": {"type": "string"}
                            },
                            "required": ["type", "description"]
                        }
                    }
                },
                "required": ["section_title", "items"]
            }
        }
    },
    "required": ["title", "intent", "sections"]
}
