package practice.model;

import java.math.BigInteger;
import java.util.*;
import practice.io.DataValidator;

/** Validated snapshot. Collections cannot be modified through this API. */
public final class DataSet {
    private final List<Order> orders;
    private final List<ComponentModel> models;
    private final List<SpecificationItem> spec_items;
    private final List<TestPlan> plans;
    private final List<TestDefinition> tests;
    private final List<PlanTest> plan_tests;
    private final List<TestRun> runs;
    private final List<Component> components;
    private final List<RunComponent> run_components;
    private final List<TestResult> results;
    private final List<Defect> defects;

    public DataSet(Object input) {
        Map<String, List<Map<String, Object>>> data = new DataValidator().validate(input);
        orders = data.get("orders").stream().map(row -> new Order((BigInteger) row.get("id"), (String) row.get("number"), (String) row.get("purpose"), (String) row.get("spec_version"), (String) row.get("server_serial"))).toList();
        models = data.get("models").stream().map(row -> new ComponentModel((BigInteger) row.get("id"), (String) row.get("kind"), (String) row.get("name"))).toList();
        spec_items = data.get("spec_items").stream().map(row -> new SpecificationItem((BigInteger) row.get("order_id"), (BigInteger) row.get("model_id"), (BigInteger) row.get("quantity"))).toList();
        plans = data.get("plans").stream().map(row -> new TestPlan((BigInteger) row.get("id"), (String) row.get("version"))).toList();
        tests = data.get("tests").stream().map(row -> new TestDefinition((BigInteger) row.get("id"), (String) row.get("code"), (String) row.get("name"))).toList();
        plan_tests = data.get("plan_tests").stream().map(row -> new PlanTest((BigInteger) row.get("plan_id"), (BigInteger) row.get("test_id"))).toList();
        runs = data.get("runs").stream().map(row -> new TestRun((BigInteger) row.get("id"), (BigInteger) row.get("order_id"), (BigInteger) row.get("plan_id"), (BigInteger) row.get("number"), (String) row.get("engineer"), (String) row.get("bios"), (String) row.get("bmc"))).toList();
        components = data.get("components").stream().map(row -> new Component((BigInteger) row.get("id"), (String) row.get("serial"), (BigInteger) row.get("model_id"))).toList();
        run_components = data.get("run_components").stream().map(row -> new RunComponent((BigInteger) row.get("run_id"), (BigInteger) row.get("component_id"))).toList();
        results = data.get("results").stream().map(row -> new TestResult((BigInteger) row.get("run_id"), (BigInteger) row.get("test_id"), (String) row.get("status"), (String) row.get("log_ref"), (String) row.get("parameters"), (String) row.get("performed_at"))).toList();
        defects = data.get("defects").stream().map(row -> new Defect((BigInteger) row.get("id"), (BigInteger) row.get("run_id"), (String) row.get("description"), (String) row.get("status"))).toList();
    }
    public List<Order> orders() { return orders; }
    public List<ComponentModel> models() { return models; }
    public List<SpecificationItem> spec_items() { return spec_items; }
    public List<TestPlan> plans() { return plans; }
    public List<TestDefinition> tests() { return tests; }
    public List<PlanTest> plan_tests() { return plan_tests; }
    public List<TestRun> runs() { return runs; }
    public List<Component> components() { return components; }
    public List<RunComponent> run_components() { return run_components; }
    public List<TestResult> results() { return results; }
    public List<Defect> defects() { return defects; }
}
