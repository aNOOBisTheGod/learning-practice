package ru.practice;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonParseException;
import com.google.gson.Strictness;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

public final class Check {
    public static void main(String[] args) {
        System.exit(run(args));
    }

    static int run(String[] args) {
        if (args.length != 1) {
            System.err.println("Использование: java -jar java/target/protocol-check.jar <протокол.json>");
            return 64;
        }
        Gson gson = new GsonBuilder().setStrictness(Strictness.STRICT)
                .setPrettyPrinting().disableHtmlEscaping().create();
        try {
            String text = Files.readString(Path.of(args[0]), StandardCharsets.UTF_8);
            Protocol protocol = Protocol.fromJson(gson.fromJson(text, JsonElement.class));
            var result = new ProtocolEvaluator().evaluate(protocol);
            System.out.println(gson.toJson(result));
            return result.ready() ? 0 : 1;
        } catch (JsonParseException | IllegalArgumentException error) {
            System.err.println("Ошибка входных данных: " + error.getMessage());
            return 64;
        } catch (IOException error) {
            System.err.println("Не удалось прочитать файл: " + error.getMessage());
            return 64;
        }
    }
}
