package practice.model;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;

/** Immutable row of results; references retain the keys of KT2. */
public record TestResult(BigInteger run_id, BigInteger test_id, String status, String log_ref, String parameters, String performed_at) {
    public Map<String, Object> toMap() {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("run_id", run_id);
        row.put("test_id", test_id);
        row.put("status", status);
        row.put("log_ref", log_ref);
        row.put("parameters", parameters);
        row.put("performed_at", performed_at);
        return row;
    }
}
