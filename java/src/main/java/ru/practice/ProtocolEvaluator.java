package ru.practice;

import java.util.ArrayList;
import java.util.List;

public final class ProtocolEvaluator {
    public record Result(String order, String serial, String plan,
                         boolean ready, List<String> reasons) {
        public Result {
            reasons = List.copyOf(reasons);
        }
    }

    public Result evaluate(Protocol protocol) {
        List<String> reasons = new ArrayList<>();
        if (!protocol.configurationMatches()) {
            reasons.add("Комплектация не соответствует спецификации");
        }
        if (protocol.openDefects().signum() != 0) {
            reasons.add("Есть незакрытые дефекты");
        }
        for (String name : Protocol.REQUIRED_CHECKS) {
            String status = protocol.checks().getOrDefault(name, "missing");
            if (!status.equals("pass")) {
                reasons.add(name + ": " + status);
            }
        }
        return new Result(protocol.order(), protocol.serial(), protocol.plan(),
                reasons.isEmpty(), reasons);
    }
}
