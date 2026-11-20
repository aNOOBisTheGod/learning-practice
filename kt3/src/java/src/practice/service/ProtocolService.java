package practice.service;

import java.math.BigInteger;
import java.util.*;
import java.util.stream.Collectors;
import practice.model.*;
import practice.rules.AcceptanceRule;

/** Selects domain objects and applies injected rules in a stable order. */
public final class ProtocolService {
    private final DataSet data;
    private final List<AcceptanceRule> rules;

    public ProtocolService(DataSet data, List<AcceptanceRule> rules) {
        this.data = Objects.requireNonNull(data);
        this.rules = List.copyOf(rules);
        if (this.rules.isEmpty()) throw new IllegalArgumentException("Нужны правила проверки");
    }

    public RunContext context(BigInteger runId) {
        TestRun run = data.runs().stream().filter(r -> r.id().equals(runId)).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("Не найден прогон " + runId));
        Order order = data.orders().stream().filter(o -> o.id().equals(run.order_id()))
                .findFirst().orElseThrow();
        TestPlan plan = data.plans().stream().filter(p -> p.id().equals(run.plan_id()))
                .findFirst().orElseThrow();
        Set<BigInteger> componentIds = data.run_components().stream()
                .filter(link -> link.run_id().equals(runId)).map(RunComponent::component_id)
                .collect(Collectors.toSet());
        Set<BigInteger> orderRunIds = data.runs().stream()
                .filter(r -> r.order_id().equals(order.id())).map(TestRun::id)
                .collect(Collectors.toSet());
        return new RunContext(order, plan, run,
                data.spec_items().stream().filter(s -> s.order_id().equals(order.id())).toList(),
                data.components().stream().filter(c -> componentIds.contains(c.id())).toList(),
                data.results().stream().filter(r -> r.run_id().equals(runId)).toList(),
                data.defects().stream().filter(d -> orderRunIds.contains(d.run_id())).toList(),
                Math.toIntExact(data.plan_tests().stream()
                        .filter(link -> link.plan_id().equals(plan.id())).count()));
    }

    public Map<String, Object> buildProtocol(BigInteger runId) {
        RunContext context = context(runId);
        List<String> reasons = new ArrayList<>();
        for (AcceptanceRule rule : rules) reasons.addAll(rule.check(context));
        Map<String, Object> protocol = new LinkedHashMap<>();
        protocol.put("order", context.order().number());
        protocol.put("serial", context.order().server_serial());
        protocol.put("spec_version", context.order().spec_version());
        protocol.put("plan", context.plan().version());
        protocol.put("run_id", context.run().id());
        protocol.put("run_number", context.run().number());
        protocol.put("engineer", context.run().engineer());
        protocol.put("bios", context.run().bios());
        protocol.put("bmc", context.run().bmc());
        protocol.put("configuration", context.components().stream().map(Component::toMap).toList());
        protocol.put("results", context.results().stream().map(TestResult::toMap).toList());
        protocol.put("defects", context.defects().stream().map(Defect::toMap).toList());
        protocol.put("ready", reasons.isEmpty());
        protocol.put("reasons", List.copyOf(reasons));
        return Collections.unmodifiableMap(protocol);
    }
}
