import java.nio.file.Files;
import java.nio.file.Path;
import org.neo4j.server.CommunityBootstrapper;
import org.neo4j.server.NeoBootstrapper;

/** Project-local lifecycle adapter; stop() flushes stores and indexes before exit. */
public final class LocalNeo4j {
    public static void main(String[] args) throws Exception {
        String marker = System.getenv("ECOMMERCE_NEO4J_STOP_FILE");
        if (marker == null || marker.isBlank()) throw new IllegalArgumentException("Owned stop marker required");
        Path stopFile = Path.of(marker).toAbsolutePath().normalize();
        CommunityBootstrapper bootstrapper = new CommunityBootstrapper();
        int result = NeoBootstrapper.start(bootstrapper, args);
        if (result != 0) System.exit(result);
        while (!Files.exists(stopFile)) Thread.sleep(200);
        int stopped = bootstrapper.stop();
        Files.deleteIfExists(stopFile);
        System.exit(stopped);
    }
}
