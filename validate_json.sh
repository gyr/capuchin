 #!/bin/bash

if [[ -z "$1" ]]; then
    printf "Usage: %s <json_file>\n" "$0" >&2
    exit 1
fi

TARGET_FILE="$1"
TMP_FILE=$(mktemp)
trap 'rm -f "$TMP_FILE"' EXIT

if ! command -v jq &> /dev/null; then
    printf "Error: 'jq' is not installed.\n" >&2
    exit 1
fi

# 1. Determine if the JSON is an Array or an Object
# 'type' returns "array", "object", "string", etc.
JSON_TYPE=$(jq -r 'type' "$TARGET_FILE" 2>/dev/null)

if [[ "$JSON_TYPE" == "array" ]]; then
    printf "Detected JSON Array. Sorting elements...\n"
    JQ_FILTER="sort"
elif [[ "$JSON_TYPE" == "object" ]]; then
    printf "Detected JSON Object. Sorting keys (-S)...\n"
    # For objects, we use the -S flag and the identity filter '.'
    JQ_FILTER="."
    EXTRA_FLAGS="-S"
else
    printf "Error: %s is not a valid JSON Array or Object (Type: %s).\n" "$TARGET_FILE" "$JSON_TYPE" >&2
    exit 1
fi

# 2. Execute the appropriate sort
if jq $EXTRA_FLAGS "$JQ_FILTER" "$TARGET_FILE" > "$TMP_FILE"; then
    mv "$TMP_FILE" "$TARGET_FILE"
    printf "Successfully processed: %s\n" "$TARGET_FILE"
else
    printf "Error: Failed to process %s.\n" "$TARGET_FILE" >&2
    exit 1
fi
