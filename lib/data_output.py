import logging
import os
import json

def write_dataframe_to_csv(df, path_candidates):
    """
    Write the DataFrame to CSV and JSON (records) at the first available path in path_candidates.
    Both formats are always written for downstream use or inspection.
    """
    for candidate_path in path_candidates:
        try:
            print(f"[dwdforecast] Writing data to CSV and JSON: {candidate_path} / {os.path.splitext(candidate_path)[0] + '.json'}")
            df.to_csv(candidate_path, index=False)
            # Write JSON alongside CSV
            json_file = os.path.splitext(candidate_path)[0] + '.json'
            df.to_json(json_file, orient='records', lines=False, force_ascii=False)
            print(f"[dwdforecast] Data written successfully: {candidate_path} (CSV), {json_file} (JSON)")
            return candidate_path
        except Exception as e:
            print(f"[dwdforecast] ERROR: Could not write CSV/JSON to {candidate_path}: {e}")
            logging.error("Could not write CSV/JSON to %s: %s", candidate_path, e)
    print("[dwdforecast] ERROR: Could not write CSV/JSON to any configured path.")
    logging.error("Could not write CSV/JSON to any configured path.")
    return None
