package practice;

import java.io.IOException;
import java.io.PrintStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import practice.io.Json;
import practice.model.DataSet;
import practice.rules.ConfigurationRule;
import practice.rules.ProtocolRule;
import practice.service.ProtocolService;

/** CLI adapter; business operations belong to ProtocolService and rule objects. */
public final class Main {
    private Main() { }

    public static void main(String[] args) {
        System.exit(run(args, System.out, System.err));
    }

    public static int run(String[] args, PrintStream out, PrintStream err) {
        if (List.of(args).contains("--help") || List.of(args).contains("-h")) {
            out.println("java -cp out practice.Main DATA.json --run ID [--output PROTOCOL.json]");
            return 0;
        }
        Path input = null;
        Path output = null;
        BigInteger runId = null;
        try {
            for (int i = 0; i < args.length; i++) {
                switch (args[i]) {
                    case "--run" -> runId = new BigInteger(args[++i]);
                    case "--output" -> output = Path.of(args[++i]);
                    default -> {
                        if (input != null || args[i].startsWith("--"))
                            throw new IllegalArgumentException("Неизвестный аргумент " + args[i]);
                        input = Path.of(args[i]);
                    }
                }
            }
            if (input == null || runId == null) throw new IllegalArgumentException("Нужны DATA.json и --run ID");
        } catch (IllegalArgumentException | IndexOutOfBoundsException error) {
            err.println("Ошибка аргументов: " + error.getMessage());
            return 2;
        }
        try {
            DataSet data = new DataSet(new Json(Files.readString(input, StandardCharsets.UTF_8)).parse());
            ProtocolService service = new ProtocolService(data,
                    List.of(new ConfigurationRule(), new ProtocolRule()));
            Map<String, Object> protocol = service.buildProtocol(runId);
            if (output != null) Files.writeString(output, Json.stringify(protocol) + "\n", StandardCharsets.UTF_8);
            out.println("Заявка: " + protocol.get("order") + "; сервер: " + protocol.get("serial")
                    + "; прогон: " + protocol.get("run_number"));
            out.println("Спецификация: " + protocol.get("spec_version") + "; план: " + protocol.get("plan"));
            boolean ready = Boolean.TRUE.equals(protocol.get("ready"));
            out.println("Предварительный допуск: " + (ready ? "ДА" : "НЕТ"));
            for (Object reason : (List<?>) protocol.get("reasons")) out.println("- " + reason);
            return ready ? 0 : 1;
        } catch (IOException | IllegalArgumentException error) {
            err.println("Ошибка: " + error.getMessage());
            return 64;
        }
    }
}
