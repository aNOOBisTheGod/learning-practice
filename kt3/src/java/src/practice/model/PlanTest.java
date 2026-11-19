package practice.model;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;

/** Immutable row of plan_tests; references retain the keys of KT2. */
public record PlanTest(BigInteger plan_id, BigInteger test_id) {
    public Map<String, Object> toMap() {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("plan_id", plan_id);
        row.put("test_id", test_id);
        return row;
    }
}
