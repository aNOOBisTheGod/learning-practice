package practice.rules;

import java.util.ArrayList;
import java.util.List;
import practice.io.Json;
import practice.model.Defect;
import practice.model.RunContext;
import practice.model.TestResult;

/** KT2 algorithm 2: result completeness, journals and open defects. */
public final class ProtocolRule extends AbstractAcceptanceRule {
    @Override
    protected List<String> evaluate(RunContext context) {
        List<String> reasons = new ArrayList<>();
        for (TestResult result : context.results()) {
            if (!result.status().equals("pass")) {
                reasons.add("Тест " + result.test_id() + ": " + result.status());
            }
            if (Json.blank(result.log_ref()) || Json.blank(result.performed_at())) {
                reasons.add("Тест " + result.test_id() + ": нет журнала или времени");
            }
        }
        int missing = context.requiredCount() - context.results().size();
        if (missing > 0) reasons.add("Пропущено обязательных тестов: " + missing);
        for (Defect defect : context.defects()) {
            if (defect.status().equals("open")) {
                reasons.add("Открыт дефект " + defect.id() + ": " + defect.description());
            }
        }
        return reasons;
    }
}
