package practice.model;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;

/** Immutable row of orders; references retain the keys of KT2. */
public record Order(BigInteger id, String number, String purpose, String spec_version, String server_serial) {
    public Map<String, Object> toMap() {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", id);
        row.put("number", number);
        row.put("purpose", purpose);
        row.put("spec_version", spec_version);
        row.put("server_serial", server_serial);
        return row;
    }
}
