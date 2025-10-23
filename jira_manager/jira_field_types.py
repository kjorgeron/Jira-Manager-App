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
    def extract_display_value(self, field_type, raw_value):
        """
        Extract a user-friendly display value for a field, using the display_key if available.
        Handles JSON strings and Python dict strings robustly.
        """
        print(f"{field_type=}")
        field_info = self.get(field_type)
        if not field_info or not raw_value:
            return raw_value
        key = field_info.display_key
        if not key:
            return raw_value
        try:
            obj = raw_value
            if isinstance(raw_value, str):
                try:
                    obj = json.loads(raw_value)
                except Exception:
                    try:
                        obj = ast.literal_eval(raw_value)
                    except Exception:
                        pass
            if field_type in ("option_multi", "version", "attachment"):
                if isinstance(obj, list):
                    return ", ".join(str(o.get(key, o)) for o in obj if isinstance(o, dict))
            if field_type.lower() == "comment" and isinstance(obj, dict) and "comments" in obj:
                return obj["comments"]
            if isinstance(obj, dict):
                val = obj.get(key)
                if val is not None:
                    return val
            return raw_value
        except Exception:
            return raw_value
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
            '"labels": ["bug", "urgent"]',
            "List of strings.",
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
