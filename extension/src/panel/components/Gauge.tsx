interface GaugeProps {
  score: number; // 0 a 100
  classification: "verdadeiro" | "moderado" | "falso" | "inconclusivo";
}

export function Gauge({ score, classification }: GaugeProps) {
  // Converte score (0-100) em rotação de ponteiro (-90deg a +90deg)
  const angle = Math.min(Math.max((score / 100) * 180 - 90, -90), 90);

  const getStatusColor = () => {
    switch (classification) {
      case "verdadeiro":
        return "var(--color-veracidade-apoiada)";
      case "moderado":
        return "var(--color-veracidade-moderada)";
      case "falso":
        return "var(--color-veracidade-falsa)";
      default:
        return "var(--color-veracidade-inconclusiva)";
    }
  };

  return (
    <div
      class="card"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "16px",
      }}
      role="region"
      aria-label={`Índice de veracidade apurado: ${score} por cento, classificado como ${classification}`}
    >
      <div style={{ position: "relative", width: "180px", height: "100px", overflow: "hidden" }}>
        {/* Arco Graduado Tricolor (SVG) */}
        <svg viewBox="0 0 100 50" style={{ width: "100%", height: "100%" }}>
          <path
            d="M 10 50 A 40 40 0 0 1 90 50"
            fill="none"
            stroke="#3F3F3F"
            stroke-width="10"
          />
          <path
            d="M 10 50 A 40 40 0 0 1 36 21"
            fill="none"
            stroke="var(--color-veracidade-falsa)"
            stroke-width="10"
          />
          <path
            d="M 36 21 A 40 40 0 0 1 64 21"
            fill="none"
            stroke="var(--color-veracidade-moderada)"
            stroke-width="10"
          />
          <path
            d="M 64 21 A 40 40 0 0 1 90 50"
            fill="none"
            stroke="var(--color-veracidade-apoiada)"
            stroke-width="10"
          />
        </svg>

        {/* Ponteiro central */}
        <div
          style={{
            position: "absolute",
            bottom: "0",
            left: "50%",
            width: "4px",
            height: "45px",
            background: "#FFFFFF",
            transformOrigin: "bottom center",
            transform: `translateX(-50%) rotate(${angle}deg)`,
            transition: "transform 0.8s cubic-bezier(0.4, 0, 0.2, 1)",
            borderRadius: "2px",
          }}
        />
        <div
          style={{
            position: "absolute",
            bottom: "-6px",
            left: "50%",
            transform: "translateX(-50%)",
            width: "12px",
            height: "12px",
            background: "#FFFFFF",
            borderRadius: "50%",
          }}
        />
      </div>

      <div style={{ marginTop: "12px", textAlign: "center" }}>
        <div
          style={{
            fontSize: "24px",
            fontWeight: "700",
            color: getStatusColor(),
          }}
        >
          {score}%
        </div>
        <div
          style={{
            fontSize: "12px",
            fontWeight: "600",
            textTransform: "uppercase",
            letterSpacing: "0.5px",
            color: getStatusColor(),
          }}
        >
          {classification}
        </div>
      </div>
    </div>
  );
}
