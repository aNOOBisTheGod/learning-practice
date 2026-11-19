package practice.model;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;

/** Immutable row of models; references retain the keys of KT2. */
public record ComponentModel(BigInteger id, String kind, String name) {
    public Map<String, Object> toMap() {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", id);
        row.put("kind", kind);
        row.put("name", name);
        return row;
    }
}
