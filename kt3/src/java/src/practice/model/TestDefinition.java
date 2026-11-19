package practice.model;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;

/** Immutable row of tests; references retain the keys of KT2. */
public record TestDefinition(BigInteger id, String code, String name) {
    public Map<String, Object> toMap() {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", id);
        row.put("code", code);
        row.put("name", name);
        return row;
    }
}
