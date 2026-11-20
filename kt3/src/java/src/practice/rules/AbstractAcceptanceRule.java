package practice.rules;

import java.util.List;
import java.util.Objects;
import practice.model.RunContext;

/** Template method: validate the context, run the specific check, freeze the result. */
public abstract class AbstractAcceptanceRule implements AcceptanceRule {
    @Override
    public final List<String> check(RunContext context) {
        Objects.requireNonNull(context, "context");
        return List.copyOf(evaluate(context));
    }

    protected abstract List<String> evaluate(RunContext context);
}
