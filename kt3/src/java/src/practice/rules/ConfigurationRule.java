package practice.rules;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import practice.model.Component;
import practice.model.RunContext;
import practice.model.SpecificationItem;

/** KT2 algorithm 1: full nested scan, followed by detection of extra components. */
public final class ConfigurationRule extends AbstractAcceptanceRule {
    @Override
    protected List<String> evaluate(RunContext context) {
        List<String> issues = new ArrayList<>();
        List<Boolean> matched = new ArrayList<>(Collections.nCopies(context.components().size(), false));
        for (SpecificationItem item : context.specification()) {
            int actual = 0;
            for (int j = 0; j < context.components().size(); j++) {
                Component component = context.components().get(j);
                if (component.model_id().equals(item.model_id())) {
                    actual++;
                    matched.set(j, true);
                }
            }
            if (!item.quantity().equals(BigInteger.valueOf(actual))) {
                issues.add("Модель " + item.model_id() + ": нужно " + item.quantity()
                        + ", найдено " + actual);
            }
        }
        for (int j = 0; j < context.components().size(); j++) {
            Component component = context.components().get(j);
            if (!matched.get(j)) {
                issues.add("Лишний компонент: " + component.serial());
            }
        }
        return issues;
    }
}
