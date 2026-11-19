package practice.model;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;

/** Immutable row of run_components; references retain the keys of KT2. */
public record RunComponent(BigInteger run_id, BigInteger component_id) {
    public Map<String, Object> toMap() {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("run_id", run_id);
        row.put("component_id", component_id);
        return row;
    }
}
