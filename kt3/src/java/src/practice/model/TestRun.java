package practice.model;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;

/** Immutable row of runs; references retain the keys of KT2. */
public record TestRun(BigInteger id, BigInteger order_id, BigInteger plan_id, BigInteger number, String engineer, String bios, String bmc) {
    public Map<String, Object> toMap() {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", id);
        row.put("order_id", order_id);
        row.put("plan_id", plan_id);
        row.put("number", number);
        row.put("engineer", engineer);
        row.put("bios", bios);
        row.put("bmc", bmc);
        return row;
    }
}
