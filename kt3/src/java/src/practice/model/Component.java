package practice.model;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;

/** Immutable row of components; references retain the keys of KT2. */
public record Component(BigInteger id, String serial, BigInteger model_id) {
    public Map<String, Object> toMap() {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", id);
        row.put("serial", serial);
        row.put("model_id", model_id);
        return row;
    }
}
