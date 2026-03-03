import logging

def write_dataframe_to_csv(df, path_candidates):
    """
    Try to write the DataFrame to the first available path in path_candidates.
    Returns the path used if successful, or None if all fail.
    """
    for candidate_path in path_candidates:
        try:
            print(f"[dwdforecast] Attempting to write CSV: {candidate_path}")
            df.to_csv(candidate_path)
            print(f"[dwdforecast] CSV written successfully: {candidate_path}")
            return candidate_path
        except Exception as e:
            print(f"[dwdforecast] ERROR: Could not write CSV to {candidate_path}: {e}")
            logging.error("Could not write CSV to %s: %s", candidate_path, e)
    print("[dwdforecast] ERROR: Could not write CSV to any configured path.")
    logging.error("Could not write CSV to any configured path.")
    return None

