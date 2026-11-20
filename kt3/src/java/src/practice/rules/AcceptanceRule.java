package practice.rules;

import java.util.List;
import practice.model.RunContext;

/** A rule returns every reason for refusal; an empty list means success. */
public interface AcceptanceRule {
    List<String> check(RunContext context);
}
