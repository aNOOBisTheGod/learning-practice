package practice.model;

import java.util.List;
import java.util.Objects;

/** Immutable selection for one run; defects cover every run of the same order. */
public record RunContext(Order order, TestPlan plan, TestRun run,
                         List<SpecificationItem> specification, List<Component> components,
                         List<TestResult> results, List<Defect> defects, int requiredCount) {
    public RunContext {
        Objects.requireNonNull(order);
        Objects.requireNonNull(plan);
        Objects.requireNonNull(run);
        specification = List.copyOf(specification);
        components = List.copyOf(components);
        results = List.copyOf(results);
        defects = List.copyOf(defects);
        if (requiredCount < 0) throw new IllegalArgumentException("Отрицательное число тестов");
    }
}
