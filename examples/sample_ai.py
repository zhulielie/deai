import os
import json
from typing import List, Dict, Optional


def process_user_data(user_list: List[Dict], output_directory: str, verbose: bool = True) -> Optional[str]:
    """
    Process a list of user dictionaries and write the result to a JSON file.
    """
    if user_list is None:
        return None

    processed_results = []
    for user in user_list:
        if not user.get("is_active"):
            continue

        user_id = user["id"]
        user_name = user["name"]
        user_email = user["email"]

        processed_item = {
            "id": user_id,
            "name": user_name,
            "email": user_email,
            "status": "active"
        }
        processed_results.append(processed_item)

    if len(processed_results) == 0:
        return None

    output_path = os.path.join(output_directory, "result.json")
    with open(output_path, "w", encoding="utf-8") as file_handle:
        json.dump(processed_results, file_handle, indent=2)

    if verbose:
        print(f"Successfully wrote {len(processed_results)} records to {output_path}")

    return output_path
