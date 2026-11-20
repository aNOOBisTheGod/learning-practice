import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import practice.io.Json;
import practice.model.*;
import practice.rules.*;
import practice.service.ProtocolService;

/** Standalone contract tests, without third-party libraries or Python. */
public final class SelfTest {
    private static int checks;
    private SelfTest() { }
    private static void check(boolean condition, String label) {
        if (!condition) throw new AssertionError(label);
        checks++;
    }
    private static void rejects(Runnable action, String label) {
        try { action.run(); }
        catch (IllegalArgumentException | UnsupportedOperationException | NullPointerException expected) {
            checks++; return;
        }
        throw new AssertionError(label);
    }
    private static ProtocolService service(DataSet data) {
        return new ProtocolService(data, List.of(new ConfigurationRule(), new ProtocolRule()));
    }
    @SuppressWarnings("unchecked")
    private static Map<String, Object> input(String text) { return (Map<String, Object>) new Json(text).parse(); }
    @SuppressWarnings("unchecked")
    private static List<Map<String, Object>> rows(Map<String, Object> data, String table) {
        return (List<Map<String, Object>>) data.get(table);
    }
    public static void main(String[] args) throws Exception {
        String text = Files.readString(Path.of("examples/data.json"), StandardCharsets.UTF_8);
        DataSet data = new DataSet(new Json(text).parse());
        ProtocolService service = service(data);
        BigInteger one = BigInteger.ONE, two = BigInteger.TWO;
        Map<String, Object> passed = service.buildProtocol(two);
        check(Boolean.TRUE.equals(passed.get("ready")), "second run accepted");
        check(service.buildProtocol(one).get("reasons").equals(List.of("Тест 2: fail")), "first run refused");
        check(passed.get("configuration") instanceof List<?> list && list.size() == 4, "all components exported");
        check(passed.get("defects") instanceof List<?> list && list.size() == 1, "history exported");
        rejects(() -> data.orders().clear(), "immutable dataset");
        rejects(() -> service.context(two).results().clear(), "immutable context");
        rejects(() -> service.buildProtocol(BigInteger.valueOf(999)), "unknown run");
        rejects(() -> new ProtocolService(data, List.of()), "empty rules");
        AcceptanceRule config = new ConfigurationRule(), protocol = new ProtocolRule();
        check(config instanceof AbstractAcceptanceRule && protocol instanceof AbstractAcceptanceRule, "real hierarchy");
        check(config.check(service.context(one)).isEmpty(), "config succeeds independently");
        check(!protocol.check(service.context(one)).isEmpty(), "protocol has different behavior");
        rejects(() -> protocol.check(null), "base class rejects null");
        rejects(() -> protocol.check(service.context(one)).clear(), "base class freezes result");
        List<AcceptanceRule> injected = new ArrayList<>(List.of(config, protocol));
        ProtocolService copied = new ProtocolService(data, injected);
        injected.clear();
        check(copied.buildProtocol(two).equals(passed), "defensive rule collection");
        // A new rule is passed through the interface without changes in ProtocolService.
        AcceptanceRule additional = context -> List.of("Проверка инженера обязательна");
        ProtocolService extended = new ProtocolService(data, List.of(config, protocol, additional));
        check(extended.buildProtocol(two).get("reasons").equals(List.of("Проверка инженера обязательна")), "extension point");
        Map<String, Object> source = input(text);
        DataSet snapshot = new DataSet(source);
        rows(source, "runs").get(1).put("engineer", "changed");
        check(!snapshot.runs().get(1).engineer().equals("changed"), "input alias isolation");
        for (String table : source.keySet()) {
            Map<String, Object> duplicate = input(text);
            rows(duplicate, table).add(new LinkedHashMap<>(rows(duplicate, table).get(0)));
            rejects(() -> new DataSet(duplicate), "duplicate " + table);
        }
        for (String state : List.of("fail", "pending")) {
            Map<String, Object> changed = input(text);
            rows(changed, "results").get(11).put("status", state);
            check(Boolean.FALSE.equals(service(new DataSet(changed)).buildProtocol(two).get("ready")), state);
        }
        Map<String, Object> changed = input(text);
        rows(changed, "defects").get(0).put("status", "open");
        check(Boolean.FALSE.equals(service(new DataSet(changed)).buildProtocol(two).get("ready")), "old defect blocks");
        Map<String, Object> early = input(text);
        rows(early, "runs").remove(1);
        early.put("run_components", List.of()); early.put("results", List.of());
        rows(early, "defects").get(0).put("status", "open");
        var earlyReport = service(new DataSet(early)).buildProtocol(one);
        check(Boolean.FALSE.equals(earlyReport.get("ready")), "early rejection");
        check(((List<?>) earlyReport.get("reasons")).contains("Пропущено обязательных тестов: 6"), "early missing tests");
        for (String invalid : List.of("{", "[1,]", "{\"a\":1,\"a\":2}", "NaN", "01", "1.", "true false", "\"\\q\"")) {
            rejects(() -> new Json(invalid).parse(), "invalid JSON " + invalid);
        }
        Object roundTrip = new Json("{\"text\":\"Иван 😀\\n\\t\\\"\",\"id\":999999999999999999999999999999999999}").parse();
        check(new Json(Json.stringify(roundTrip)).parse().equals(roundTrip), "Unicode and BigInteger roundtrip");
        check(new Json("[true,false,null,-1,1.25,2e3]").parse() instanceof List<?> list && list.size()==6, "JSON types");
        check(Json.blank("\u0085\u00a0\u2003"), "Python whitespace");
        check(service.buildProtocol(two).equals(passed), "repeat evaluation preserves history");
        System.out.println("PASS: " + checks + " Java checks");
    }
}
