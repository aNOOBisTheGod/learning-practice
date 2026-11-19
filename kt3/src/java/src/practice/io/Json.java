package practice.io;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.*;

/** Small JSON codec; rejects duplicate members and non-JSON numeric constants. */
public final class Json {
    private final String text;
    private int position;
    public Json(String text) { this.text = Objects.requireNonNull(text); }
    public Object parse() {
        Object result = value(0);
        whitespace();
        if (position != text.length()) throw error("Лишние символы");
        return result;
    }
    private IllegalArgumentException error(String message) {
        return new IllegalArgumentException(message + " (JSON, позиция " + position + ")");
    }
    private void whitespace() {
        while (position < text.length() && " \n\r\t".indexOf(text.charAt(position)) >= 0) position++;
    }
    private boolean take(char token) {
        whitespace();
        if (position < text.length() && text.charAt(position) == token) { position++; return true; }
        return false;
    }
    private void expect(char token) { if (!take(token)) throw error("Ожидался " + token); }
    private Object value(int depth) {
        if (depth > 256) throw error("Слишком большая вложенность");
        whitespace();
        if (position == text.length()) throw error("Неожиданный конец");
        char ch = text.charAt(position);
        if (ch == '"') return string();
        if (take('{')) {
            Map<String, Object> result = new LinkedHashMap<>();
            if (take('}')) return result;
            do {
                whitespace();
                String key = string();
                expect(':');
                if (result.containsKey(key)) throw error("Повторяющееся поле " + key);
                result.put(key, value(depth + 1));
            } while (take(','));
            expect('}'); return result;
        }
        if (take('[')) {
            List<Object> result = new ArrayList<>();
            if (take(']')) return result;
            do { result.add(value(depth + 1)); } while (take(','));
            expect(']'); return result;
        }
        for (String literal : List.of("true", "false", "null")) {
            if (text.startsWith(literal, position)) {
                position += literal.length();
                return literal.equals("null") ? null : Boolean.valueOf(literal);
            }
        }
        int start = position;
        if (text.charAt(position) == '-') position++;
        if (position >= text.length()) throw error("Нет числа");
        if (text.charAt(position) == '0') position++;
        else {
            int before = position;
            while (position < text.length() && digit(text.charAt(position))) position++;
            if (position == before) throw error("Неверное число");
        }
        boolean decimal = false;
        if (position < text.length() && text.charAt(position) == '.') {
            decimal = true; position++; digits();
        }
        if (position < text.length() && "eE".indexOf(text.charAt(position)) >= 0) {
            decimal = true; position++;
            if (position < text.length() && "+-".indexOf(text.charAt(position)) >= 0) position++;
            digits();
        }
        String number = text.substring(start, position);
        try { return decimal ? new BigDecimal(number) : new BigInteger(number); }
        catch (NumberFormatException ex) { throw error("Неверное число"); }
    }
    private boolean digit(char ch) { return ch >= '0' && ch <= '9'; }
    private void digits() {
        int before = position;
        while (position < text.length() && digit(text.charAt(position))) position++;
        if (before == position) throw error("Ожидалась цифра");
    }
    private String string() {
        if (position >= text.length() || text.charAt(position++) != '"') throw error("Нужна строка");
        StringBuilder result = new StringBuilder();
        while (position < text.length()) {
            char ch = text.charAt(position++);
            if (ch == '"') return result.toString();
            if (ch < 32) throw error("Управляющий символ в строке");
            if (ch == '\\') {
                if (position >= text.length()) throw error("Незавершённая escape-последовательность");
                char escaped = text.charAt(position++);
                switch (escaped) {
                    case '"', '\\', '/' -> result.append(escaped);
                    case 'b' -> result.append('\b');
                    case 'f' -> result.append('\f');
                    case 'n' -> result.append('\n');
                    case 'r' -> result.append('\r');
                    case 't' -> result.append('\t');
                    case 'u' -> {
                        if (position + 4 > text.length()) throw error("Неверный Unicode escape");
                        String hex = text.substring(position, position + 4);
                        if (!hex.matches("[0-9a-fA-F]{4}")) throw error("Неверный Unicode escape");
                        result.append((char) Integer.parseInt(hex, 16)); position += 4;
                    }
                    default -> throw error("Неверная escape-последовательность");
                }
            } else result.append(ch);
        }
        throw error("Строка не закрыта");
    }
    /** Python str.strip whitespace semantics for accepted textual fields. */
    public static boolean blank(String value) {
        return value.codePoints().allMatch(c -> Character.isWhitespace(c) || Character.isSpaceChar(c) || c == 0x85);
    }
    public static String stringify(Object value) {
        if (value == null) return "null";
        if (value instanceof Boolean || value instanceof Number) return value.toString();
        if (value instanceof String s) {
            StringBuilder out = new StringBuilder("\"");
            for (int i = 0; i < s.length(); i++) {
                char c = s.charAt(i);
                if (c == '"' || c == '\\') out.append('\\').append(c);
                else if (c < 32 || Character.isSurrogate(c)) out.append(String.format("\\u%04x", (int)c));
                else out.append(c);
            }
            return out.append('"').toString();
        }
        if (value instanceof Map<?, ?> map) {
            List<String> members = new ArrayList<>();
            for (var entry : map.entrySet()) members.add(stringify(entry.getKey().toString()) + ":" + stringify(entry.getValue()));
            return "{" + String.join(",", members) + "}";
        }
        if (value instanceof Collection<?> list) return "[" + String.join(",", list.stream().map(Json::stringify).toList()) + "]";
        throw new IllegalArgumentException("Неподдерживаемый тип JSON");
    }
}
