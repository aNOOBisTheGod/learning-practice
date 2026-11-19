package practice.model;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;

/** Immutable row of spec_items; references retain the keys of KT2. */
public record SpecificationItem(BigInteger order_id, BigInteger model_id, BigInteger quantity) {
    public Map<String, Object> toMap() {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("order_id", order_id);
        row.put("model_id", model_id);
        row.put("quantity", quantity);
        return row;
    }
}
