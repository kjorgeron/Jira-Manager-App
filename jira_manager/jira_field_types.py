import json
import ast

class JiraFieldType:
    """
    Represents a Jira field type and its JSON format template.
    Optionally includes a display_key for extracting display values from JSON.
    """
    def __init__(self, name, json_template, description=None, display_key=None):
        self.name = name
        self.json_template = json_template
        self.description = description or ""
        self.display_key = display_key

    def __repr__(self):
        return f"<JiraFieldType {self.name}>"

class JiraFieldTypeRegistry:
    def extract_display_value(self, field_type, raw_value, field_name=None):
        """
        Extract a user-friendly display value for a field, using the display_key if available.
        Handles JSON strings and Python dict strings robustly.
        Handles array, date, datetime, number, boolean, and custom types generically.
        """
        print(f"{field_type=}")
        field_info = self.get(field_type)
        if not field_info or raw_value is None:
            return raw_value
        key = field_info.display_key

        # Parse JSON or Python literal if needed
        obj = raw_value
        if isinstance(raw_value, str):
            try:
                obj = json.loads(raw_value)
            except Exception:
                try:
                    obj = ast.literal_eval(raw_value)
                except Exception:
                    pass



        # Generic handler for Atlassian Document Format (ADF) rich text fields
        def extract_adf_text(adf):
            # Recursively extract all text from ADF content
            if isinstance(adf, dict):
                if adf.get("type") == "text" and "text" in adf:
                    return adf["text"]
                elif "content" in adf:
                    return " ".join(extract_adf_text(child) for child in adf["content"])
            elif isinstance(adf, list):
                return " ".join(extract_adf_text(item) for item in adf)
            return ""

        # If value is Atlassian Document Format (ADF), extract plain text
        if isinstance(obj, dict) and obj.get("type") == "doc" and "content" in obj:
            text = extract_adf_text(obj)
            return (field_name or field_type, text)

        # Array: extract key and value as tuple(s) if dict, or join if list
        if field_type == "array":
            if isinstance(obj, dict):
                # If only one key, return (key, value)
                if len(obj) == 1:
                    k, v = next(iter(obj.items()))
                    return (k, v)
                # If multiple keys, return list of (key, value) tuples
                return [(k, v) for k, v in obj.items()]
            elif isinstance(obj, list):
                return (field_name or field_type, obj)
            return (field_name or field_type, obj)

        # For all other types, return (field_name, value) if not a dict with display_key
        # Datetime
        if field_type == "datetime":
            import datetime
            try:
                dt = obj
                if not isinstance(dt, (datetime.datetime, datetime.date)):
                    dt = datetime.datetime.fromisoformat(str(obj))
                return (field_name or field_type, dt.strftime("%Y-%m-%d %H:%M:%S"))
            except Exception:
                return (field_name or field_type, str(obj))

        # Date
        if field_type == "date":
            import datetime
            try:
                d = obj
                if not isinstance(d, datetime.date):
                    d = datetime.date.fromisoformat(str(obj))
                return (field_name or field_type, d.strftime("%Y-%m-%d"))
            except Exception:
                return (field_name or field_type, str(obj))

        # Number
        if field_type == "number":
            try:
                return (field_name or field_type, str(float(obj)))
            except Exception:
                return (field_name or field_type, str(obj))

        # Boolean
        if field_type == "boolean":
            return (field_name or field_type, str(bool(obj)))

        # Option multi, version, attachment: join display_key from list of dicts
        if field_type in ("option_multi", "version", "attachment"):
            if isinstance(obj, list):
                return (field_name or field_type, ", ".join(str(o.get(key, o)) for o in obj if isinstance(o, dict)))

        # Comments-page and comment
        if field_type.lower() in ("comment", "comments-page") and isinstance(obj, dict) and "comments" in obj:
            return (field_name or field_type, obj["comments"])

        # Generic dict with display_key
        if key and isinstance(obj, dict):
            val = obj.get(key)
            if val is not None:
                return (field_name or key or field_type, val)

        # Fallback: always return (field_name, value)
        return (field_name or field_type, str(obj))

        # Datetime
        if field_type == "datetime":
            import datetime
            try:
                dt = obj
                if not isinstance(dt, (datetime.datetime, datetime.date)):
                    dt = datetime.datetime.fromisoformat(str(obj))
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                return str(obj)

        # Date
        if field_type == "date":
            import datetime
            try:
                d = obj
                if not isinstance(d, datetime.date):
                    d = datetime.date.fromisoformat(str(obj))
                return d.strftime("%Y-%m-%d")
            except Exception:
                return str(obj)

        # Number
        if field_type == "number":
            try:
                return str(float(obj))
            except Exception:
                return str(obj)

        # Boolean
        if field_type == "boolean":
            return str(bool(obj))

        # Option multi, version, attachment: join display_key from list of dicts
        if field_type in ("option_multi", "version", "attachment"):
            if isinstance(obj, list):
                return ", ".join(str(o.get(key, o)) for o in obj if isinstance(o, dict))

        # Comments-page and comment
        if field_type.lower() in ("comment", "comments-page") and isinstance(obj, dict) and "comments" in obj:
            return obj["comments"]

        # Generic dict with display_key
        if key and isinstance(obj, dict):
            val = obj.get(key)
            if val is not None:
                return val

        # Fallback: string representation
        return str(obj)
    """
    Registry for all known Jira field types and their JSON templates.
    """
    def __init__(self):
        self.types = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register(JiraFieldType(
            "string",
            '"summary": "My issue summary"',
            "Simple text field.",
            display_key=None
        ))
        self.register(JiraFieldType(
            "text",
            '"description": "Longer text..."',
            "Multi-line text field.",
            display_key=None
        ))
        self.register(JiraFieldType(
            "number",
            '"customfield_10010": 42',
            "Integer or float.",
            display_key=None
        ))
        self.register(JiraFieldType(
            "date",
            '"duedate": "2025-10-22"',
            "ISO 8601 date (YYYY-MM-DD).",
            display_key=None
        ))
        self.register(JiraFieldType(
            "datetime",
            '"created": "2025-10-22T15:30:00.000+0000"',
            "ISO 8601 datetime.",
            display_key="created"
        ))
        self.register(JiraFieldType(
            "user",
            '{"accountId": "abc", "displayName": "Jane Doe"}',
            "User object.",
            display_key="displayName"
        ))
        self.register(JiraFieldType(
            "array",
            'Generic array (e.g. {"labels": ["bug", "urgent"]} or {"components": [...]})',
            "Generic array (list of strings, numbers, or objects).",
            display_key=None
        ))
        self.register(JiraFieldType(
            "option",
            '{"id": "2", "name": "High"}',
            "Single select option object.",
            display_key="name"
        ))
        self.register(JiraFieldType(
            "option_multi",
            '[{"id": "10000", "name": "UI"}]',
            "Multi-select option (list of objects).",
            display_key="name"
        ))
        self.register(JiraFieldType(
            "project",
            '{"id": "10000", "key": "PROJ"}',
            "Project object.",
            display_key="key"
        ))
        self.register(JiraFieldType(
            "version",
            '[{"id": "10001", "name": "v1.0"}]',
            "Version list.",
            display_key="name"
        ))
        self.register(JiraFieldType(
            "resolution",
            '{"id": "1", "name": "Fixed"}',
            "Resolution object.",
            display_key="name"
        ))
        self.register(JiraFieldType(
            "status",
            '{"id": "3", "name": "In Progress"}',
            "Status object.",
            display_key="name"
        ))
        self.register(JiraFieldType(
            "boolean",
            'true',
            "Boolean value.",
            display_key=None
        ))
        self.register(JiraFieldType(
            "issuetype",
            '{"id": "3", "name": "Task", "subtask": false}',
            "Issue type object.",
            display_key="name"
        ))
        self.register(JiraFieldType(
            "attachment",
            '[{"id": "10002", "filename": "log.txt"}]',
            "List of attachment objects.",
            display_key="filename"
        ))
        self.register(JiraFieldType(
            "comments-page",
            '{"comments": [ ... ]}',
            "Comment object with array of comments.",
            display_key="comments"
        ))
        self.register(JiraFieldType(
            "group",
            '{"name": "jira-users"}',
            "Group object.",
            display_key="name"
        ))
        self.register(JiraFieldType(
            "url",
            '"customfield_10013": "https://example.com"',
            "URL string.",
            display_key=None
        ))
        self.register(JiraFieldType(
            "cascading_select",
            '{"value": "Parent", "child": {"value": "Child"}}',
            "Cascading select object.",
            display_key="value"
        ))

        # Additional common Jira field types
        self.register(JiraFieldType(
            "priority",
            '{"id": "2", "name": "High"}',
            "Priority object.",
            display_key="name"
        ))
        self.register(JiraFieldType(
            "components",
            '[{"id": "10000", "name": "UI"}]',
            "Component list.",
            display_key="name"
        ))
        self.register(JiraFieldType(
            "sprint",
            '{"id": 1, "name": "Sprint 1"}',
            "Sprint object.",
            display_key="name"
        ))
        self.register(JiraFieldType(
            "epic",
            '{"id": "10002", "key": "EPIC-1", "name": "Epic Name"}',
            "Epic object.",
            display_key="name"
        ))
        self.register(JiraFieldType(
            "parent",
            '{"id": "10003", "key": "PROJ-1", "fields": {}}',
            "Parent issue object.",
            display_key="key"
        ))
        self.register(JiraFieldType(
            "timetracking",
            '{"originalEstimate": "5h", "remainingEstimate": "3h"}',
            "Timetracking object.",
            display_key="originalEstimate"
        ))
        self.register(JiraFieldType(
            "votes",
            '{"votes": 3, "hasVoted": false}',
            "Votes object.",
            display_key="votes"
        ))
        self.register(JiraFieldType(
            "watchers",
            '{"watchCount": 2, "isWatching": true}',
            "Watchers object.",
            display_key="watchCount"
        ))
        self.register(JiraFieldType(
            "progress",
            '{"progress": 50, "total": 100}',
            "Progress object.",
            display_key="progress"
        ))

    def register(self, field_type: JiraFieldType):
        self.types[field_type.name] = field_type

    def get(self, name):
        return self.types.get(name)

    def all_types(self):
        return list(self.types.values())

# Usage example:
# registry = JiraFieldTypeRegistry()
# print(registry.get("user").json_template)
