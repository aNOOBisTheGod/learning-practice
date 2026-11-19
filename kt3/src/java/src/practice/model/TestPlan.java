package practice.model;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;

/** Immutable row of plans; references retain the keys of KT2. */
public record TestPlan(BigInteger id, String version) {
    public Map<String, Object> toMap() {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", id);
        row.put("version", version);
        return row;
    }
}
