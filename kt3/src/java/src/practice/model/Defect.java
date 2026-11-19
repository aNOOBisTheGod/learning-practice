package practice.model;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;

/** Immutable row of defects; references retain the keys of KT2. */
public record Defect(BigInteger id, BigInteger run_id, String description, String status) {
    public Map<String, Object> toMap() {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", id);
        row.put("run_id", run_id);
        row.put("description", description);
        row.put("status", status);
        return row;
    }
}
