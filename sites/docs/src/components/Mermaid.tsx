import { colors, fonts } from "@democracy-watch/theme";
import { useEffect, useId, useState } from "react";

/** Diagramme Mermaid rendu côté navigateur, aux couleurs du styleguide. */
export const Mermaid = ({ chart, title }: { chart: string; title?: string }) => {
  const [svg, setSvg] = useState("");
  const [error, setError] = useState<string | null>(null);
  const id = `mermaid-${useId().replace(/[^a-zA-Z0-9]/g, "")}`;

  useEffect(() => {
    let active = true;
    import("mermaid")
      .then(async ({ default: mermaid }) => {
        mermaid.initialize({
          startOnLoad: false,
          theme: "base",
          themeVariables: {
            fontFamily: fonts.interface,
            primaryColor: colors["fond-marque"],
            primaryTextColor: colors["texte-action"],
            primaryBorderColor: colors["bordure-action"],
            lineColor: colors["texte-mention"],
            secondaryColor: colors["fond-selection"],
            tertiaryColor: colors["fond-neutre"],
            clusterBkg: colors["jaune-50"],
            clusterBorder: colors["bordure-defaut"],
          },
        });
        const result = await mermaid.render(id, chart.trim());
        if (active) setSvg(result.svg);
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : String(reason));
      });
    return () => {
      active = false;
    };
  }, [chart, id]);

  return (
    <figure className="dw-mermaid" aria-label={title}>
      {error ? <pre>{error}</pre> : null}
      <div dangerouslySetInnerHTML={{ __html: svg }} />
      {title ? <figcaption>{title}</figcaption> : null}
    </figure>
  );
};
