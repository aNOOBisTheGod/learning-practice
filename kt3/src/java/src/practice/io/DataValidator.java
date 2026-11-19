package practice.io;

import java.math.BigInteger;
import java.util.*;

/** Checks the eleven KT2 tables before creating any domain objects. */
public final class DataValidator {
    public Map<String, List<Map<String, Object>>> validate(Object input) {
        Map<String, List<String>> definitions = schema();
        if (!(input instanceof Map<?, ?> root) || !root.keySet().equals(definitions.keySet()))
            throw new IllegalArgumentException("Нужны одиннадцать наборов сущностей");
        Map<String, List<Map<String, Object>>> data = new LinkedHashMap<>();
        for (var definition : definitions.entrySet()) {
            String table = definition.getKey();
            if (!(root.get(table) instanceof List<?> rows)) throw new IllegalArgumentException(table + ": нужен список");
            List<Map<String, Object>> checked = new ArrayList<>();
            for (Object item : rows) {
                if (!(item instanceof Map<?, ?> row) || !row.keySet().equals(new HashSet<>(definition.getValue())))
                    throw new IllegalArgumentException(table + ": неверные поля");
                Map<String, Object> copy = new LinkedHashMap<>();
                for (String field : definition.getValue()) {
                    Object value = row.get(field);
                    boolean integer = field.equals("id") || field.endsWith("_id") || field.equals("quantity") || (table.equals("runs") && field.equals("number"));
                    if (integer) {
                        if (!(value instanceof BigInteger n) || n.signum() <= 0)
                            throw new IllegalArgumentException(table + "." + field + ": нужно целое положительное число");
                    } else if (!(value instanceof String s) || (!Set.of("log_ref", "performed_at").contains(field) && Json.blank(s)))
                        throw new IllegalArgumentException(table + "." + field + ": нужна непустая строка");
                    copy.put(field, value);
                }
                checked.add(Collections.unmodifiableMap(copy));
            }
            data.put(table, List.copyOf(checked));
        }
        for (String table : List.of("orders", "models", "plans", "tests", "runs", "components", "defects")) unique(data, table, "id");
        unique(data, "spec_items", "order_id", "model_id");
        unique(data, "plan_tests", "plan_id", "test_id");
        unique(data, "run_components", "run_id", "component_id");
        unique(data, "results", "run_id", "test_id");
        unique(data, "orders", "number"); unique(data, "orders", "server_serial");
        unique(data, "models", "kind", "name"); unique(data, "plans", "version");
        unique(data, "tests", "code"); unique(data, "runs", "order_id", "number");
        unique(data, "components", "model_id", "serial");
        for (String spec : List.of("spec_items order_id orders", "spec_items model_id models", "plan_tests plan_id plans", "plan_tests test_id tests", "runs order_id orders", "runs plan_id plans", "components model_id models", "run_components run_id runs", "run_components component_id components", "results run_id runs", "results test_id tests", "defects run_id runs")) {
            String[] ref = spec.split(" ");
            Set<Object> ids = new HashSet<>();
            for (var row : data.get(ref[2])) ids.add(row.get("id"));
            for (var row : data.get(ref[0])) if (!ids.contains(row.get(ref[1]))) throw new IllegalArgumentException(spec + ": отсутствует запись");
        }
        Set<List<Object>> planned = new HashSet<>();
        for (var row : data.get("plan_tests")) planned.add(List.of(row.get("plan_id"), row.get("test_id")));
        Map<Object, Object> runPlans = new HashMap<>();
        for (var row : data.get("runs")) runPlans.put(row.get("id"), row.get("plan_id"));
        for (var row : data.get("results")) {
            if (!Set.of("pass", "fail", "pending").contains(row.get("status"))) throw new IllegalArgumentException("Неизвестный статус теста");
            if (!planned.contains(List.of(runPlans.get(row.get("run_id")), row.get("test_id")))) throw new IllegalArgumentException("Тест вне плана");
        }
        for (var row : data.get("defects")) if (!Set.of("open", "closed").contains(row.get("status"))) throw new IllegalArgumentException("Неизвестный статус дефекта");
        for (var row : data.get("orders")) if (data.get("spec_items").stream().noneMatch(s -> s.get("order_id").equals(row.get("id")))) throw new IllegalArgumentException("У заявки нет спецификации");
        for (var row : data.get("plans")) if (data.get("plan_tests").stream().noneMatch(s -> s.get("plan_id").equals(row.get("id")))) throw new IllegalArgumentException("Пустой план");
        return Collections.unmodifiableMap(data);
    }
    private void unique(Map<String, List<Map<String, Object>>> data, String table, String... fields) {
        Set<List<Object>> seen = new HashSet<>();
        for (var row : data.get(table)) {
            List<Object> key = Arrays.stream(fields).map(row::get).toList();
            if (!seen.add(key)) throw new IllegalArgumentException(table + ": повтор ключа " + key);
        }
    }
    private Map<String, List<String>> schema() {
        Map<String, List<String>> fields = new LinkedHashMap<>();
        fields.put("orders", List.of("id", "number", "purpose", "spec_version", "server_serial"));
        fields.put("models", List.of("id", "kind", "name"));
        fields.put("spec_items", List.of("order_id", "model_id", "quantity"));
        fields.put("plans", List.of("id", "version"));
        fields.put("tests", List.of("id", "code", "name"));
        fields.put("plan_tests", List.of("plan_id", "test_id"));
        fields.put("runs", List.of("id", "order_id", "plan_id", "number", "engineer", "bios", "bmc"));
        fields.put("components", List.of("id", "serial", "model_id"));
        fields.put("run_components", List.of("run_id", "component_id"));
        fields.put("results", List.of("run_id", "test_id", "status", "log_ref", "parameters", "performed_at"));
        fields.put("defects", List.of("id", "run_id", "description", "status"));
        return fields;
    }
}
