package ru.practice;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public record Protocol(String order, String serial, String plan,
                       boolean configurationMatches, BigInteger openDefects,
                       Map<String, String> checks) {
    public static final List<String> REQUIRED_CHECKS =
            List.of("cpu", "memory", "storage", "network", "cooling", "power");

    public Protocol {
        checks = Map.copyOf(checks);
    }

    public static Protocol fromJson(JsonElement input) {
        if (input == null || !input.isJsonObject()) {
            throw new IllegalArgumentException("Ожидался объект JSON");
        }
        JsonObject data = input.getAsJsonObject();
        String order = requiredString(data, "order");
        String serial = requiredString(data, "serial");
        String plan = requiredString(data, "plan");
        JsonElement matches = data.get("configuration_matches");
        JsonElement defects = data.get("open_defects");
        JsonElement checks = data.get("checks");
        if (matches == null || !matches.isJsonPrimitive()
                || !matches.getAsJsonPrimitive().isBoolean()
                || defects == null || !defects.isJsonPrimitive()
                || !defects.getAsJsonPrimitive().isNumber()
                || !defects.getAsString().matches("-?[0-9]+")
                || new BigInteger(defects.getAsString()).signum() < 0
                || checks == null || !checks.isJsonObject()) {
            throw new IllegalArgumentException("Неверная конфигурация, число дефектов или checks");
        }
        Map<String, String> statuses = new LinkedHashMap<>();
        for (var entry : checks.getAsJsonObject().entrySet()) {
            JsonElement value = entry.getValue();
            if (!REQUIRED_CHECKS.contains(entry.getKey()) || !value.isJsonPrimitive()
                    || !value.getAsJsonPrimitive().isString()
                    || !List.of("pass", "fail", "pending").contains(value.getAsString())) {
                throw new IllegalArgumentException("Неизвестная проверка или результат: " + entry.getKey());
            }
            statuses.put(entry.getKey(), value.getAsString());
        }
        return new Protocol(order, serial, plan, matches.getAsBoolean(),
                new BigInteger(defects.getAsString()), statuses);
    }

    private static String requiredString(JsonObject data, String field) {
        JsonElement value = data.get(field);
        if (value == null || !value.isJsonPrimitive()
                || !value.getAsJsonPrimitive().isString()
                || value.getAsString().codePoints().allMatch(
                        c -> Character.isWhitespace(c) || Character.isSpaceChar(c))) {
            throw new IllegalArgumentException("Не заполнено поле " + field);
        }
        return value.getAsString();
    }
}
