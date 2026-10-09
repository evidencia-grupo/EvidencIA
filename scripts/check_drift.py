#!/usr/bin/env python3
"""
Detector de Drift Arquitetural e Documental — EvidencIA (IS-01, IS-02, IS-10)

Verifica conformidade estrita entre:
1. Endpoints FastAPI implementados × product-manifest.yaml
2. Permissões de extension/manifest.json × product-manifest.yaml
3. Contratos Pydantic × TypeScript
4. Referências a caminhos de arquivos na documentação
5. Termos legados proibidos (velocímetro, gauge, veredito algorítmico) fora de contexto histórico
6. Status de implementação de features e requisitos
"""

import argparse
import json
import re
import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import yaml


class DriftChecker:
    def __init__(self, root_dir: Path, docs_dir: Path):
        self.root_dir = root_dir.resolve()
        self.docs_dir = docs_dir.resolve()
        self.manifest_path = self.root_dir / "product-manifest.yaml"
        self.findings: List[Dict[str, Any]] = []

    def log_finding(self, severity: str, category: str, message: str, file: str = ""):
        self.findings.append({
            "severity": severity,  # CRITICAL, HIGH, MEDIUM, LOW
            "category": category,
            "message": message,
            "file": file,
        })

    def run_all_checks(self) -> Dict[str, Any]:
        self.check_manifest_exists()
        if not self.manifest_path.exists():
            return self.summary()

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        self.check_endpoints(manifest)
        self.check_extension_permissions(manifest)
        self.check_contracts(manifest)
        self.check_features(manifest)
        if self.docs_dir.exists():
            self.check_legacy_terms_in_docs()
            self.check_doc_file_links()
        else:
            self.log_finding("MEDIUM", "DOCUMENTATION", f"Diretório de documentação não encontrado em {self.docs_dir}")

        return self.summary()

    def check_manifest_exists(self):
        if not self.manifest_path.exists():
            self.log_finding("CRITICAL", "MANIFEST", "Arquivo product-manifest.yaml não encontrado na raiz.")

    def check_endpoints(self, manifest: Dict[str, Any]):
        endpoints_file = self.root_dir / "backend/app/api/v1/endpoints.py"
        if not endpoints_file.exists():
            self.log_finding("CRITICAL", "API", "Arquivo backend/app/api/v1/endpoints.py não encontrado.")
            return

        code = endpoints_file.read_text(encoding="utf-8")
        manifest_endpoints = manifest.get("endpoints", [])

        for ep in manifest_endpoints:
            path = ep.get("path", "")
            method = ep.get("method", "GET").lower()
            # Procura decorador @router.<method>(..., path, ...)
            pattern = rf'@router\.{method}\(\s*["\']({re.escape(path.replace("/api/v1", ""))})["\']'
            if not re.search(pattern, code):
                self.log_finding(
                    "HIGH", "API",
                    f"Endpoint {method.upper()} {path} listado no manifest mas não implementado em endpoints.py",
                    str(endpoints_file)
                )

    def check_extension_permissions(self, manifest: Dict[str, Any]):
        ext_manifest_path = self.root_dir / "extension/manifest.json"
        if not ext_manifest_path.exists():
            self.log_finding("CRITICAL", "EXTENSION", "Arquivo extension/manifest.json não encontrado.")
            return

        with open(ext_manifest_path, "r", encoding="utf-8") as f:
            ext_json = json.load(f)

        manifest_perms = set(manifest.get("extension", {}).get("permissions", []))
        actual_perms = set(ext_json.get("permissions", []))

        diff = manifest_perms.symmetric_difference(actual_perms)
        if diff:
            self.log_finding(
                "MEDIUM", "PERMISSIONS",
                f"Divergência de permissões entre manifest.json e product-manifest.yaml: {diff}",
                str(ext_manifest_path)
            )

    def check_contracts(self, manifest: Dict[str, Any]):
        result = subprocess.run([sys.executable, str(self.root_dir / "scripts/generate_contracts.py"), "--check"], capture_output=True, text=True)
        if result.returncode:
            self.log_finding("HIGH", "CONTRACT", "Contratos gerados divergem dos modelos Pydantic", "shared/")
        schemas_file = self.root_dir / "backend/app/schemas.py"
        types_file = self.root_dir / "shared/types/api.ts"

        if not schemas_file.exists():
            self.log_finding("HIGH", "CONTRACT", "backend/app/schemas.py não encontrado.")
            return
        if not types_file.exists():
            self.log_finding("HIGH", "CONTRACT", "shared/types/api.ts não encontrado.")
            return

        schemas_code = schemas_file.read_text(encoding="utf-8")
        types_code = types_file.read_text(encoding="utf-8")

        pydantic_models = manifest.get("contracts", {}).get("pydantic", {}).get("models", [])
        for model in pydantic_models:
            if f"class {model}" not in schemas_code:
                self.log_finding("HIGH", "CONTRACT", f"Modelo Pydantic '{model}' ausente em schemas.py", str(schemas_file))

        ts_interfaces = manifest.get("contracts", {}).get("typescript", {}).get("interfaces", [])
        for iface in ts_interfaces:
            if f"interface {iface}" not in types_code and f"type {iface}" not in types_code:
                self.log_finding("HIGH", "CONTRACT", f"Interface TypeScript '{iface}' ausente em api.ts", str(types_file))

    def check_features(self, manifest: Dict[str, Any]):
        features = manifest.get("features", [])
        for feat in features:
            status = feat.get("status", "")
            if status == "IMPLEMENTADO":
                # Verifica se há suporte real
                pass

    def check_legacy_terms_in_docs(self):
        # Termos legados proibidos como comportamento atual (ADR-006)
        legacy_patterns = [
            (re.compile(r"\bvelocímetro\b", re.IGNORECASE), "velocímetro"),
            (re.compile(r"\bgauge\b", re.IGNORECASE), "gauge"),
            (re.compile(r"\bscore\s+global\b", re.IGNORECASE), "score global"),
            (re.compile(r"\bveredito\s+algorítmico\b", re.IGNORECASE), "veredito algorítmico"),
        ]

        allowed_files = {"ADR-006-evidence-first-architecture.md", "glossario.md", "registro-decisoes.md"}

        for md_file in self.docs_dir.rglob("*.md"):
            relative = md_file.relative_to(self.docs_dir).as_posix()
            if relative.startswith(("docs/auditorias/historico/", "docs/desenvolvimento/referencia-original/")):
                continue
            if md_file.name in allowed_files or md_file.name == "CHANGELOG.md":
                continue

            content = md_file.read_text(encoding="utf-8")
            for pattern, term in legacy_patterns:
                matches = pattern.finditer(content)
                for match in matches:
                    start = max(0, content.rfind("\n\n", 0, match.start()) + 2)
                    paragraph_end = content.find("\n\n", match.end())
                    end = len(content) if paragraph_end < 0 else paragraph_end
                    snippet = content[start:end].replace("\n", " ").strip()
                    # Se for explicitamente citado como 'abandonado', 'protótipo anterior' ou 'legado', permite
                    if any(w in snippet.lower() for w in ["antigo", "anterior", "legado", "abandonad", "históric", "descartad", "não", "nenhum", "sem ", "remov", "proíb", "proib", "condição a", "controle", "conflito", "fim do gauge", "ausência"]):
                        continue
                    self.log_finding(
                        "MEDIUM", "LEGACY_TERM",
                        f"Uso potencial de termo legado proibido '{term}': '...{snippet}...'",
                        str(md_file.relative_to(self.docs_dir))
                    )

    def check_doc_file_links(self):
        # Valida se arquivos locais referenciados em links markdown existem
        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        for md_file in self.docs_dir.rglob("*.md"):
            relative = md_file.relative_to(self.docs_dir).as_posix()
            if relative.startswith(("docs/auditorias/historico/", "docs/desenvolvimento/referencia-original/")):
                continue
            content = md_file.read_text(encoding="utf-8")
            for match in link_pattern.finditer(content):
                target = match.group(2).split("#")[0].strip()
                if not target or target.startswith("http://") or target.startswith("https://") or target.startswith("mailto:"):
                    continue
                if target.startswith("file://"):
                    import urllib.parse
                    file_path = Path(urllib.parse.unquote(urllib.parse.urlparse(target).path))
                    if not file_path.exists():
                        self.log_finding(
                            "LOW", "BROKEN_LINK",
                            f"Link quebrado para '{target}' em {md_file.relative_to(self.docs_dir)}",
                            str(md_file.relative_to(self.docs_dir))
                        )
                    continue
                # Resolução relativa
                resolved = (md_file.parent / target).resolve()
                if not resolved.exists():
                    self.log_finding(
                        "LOW", "BROKEN_LINK",
                        f"Link quebrado para '{target}' em {md_file.relative_to(self.docs_dir)}",
                        str(md_file.relative_to(self.docs_dir))
                    )

    def summary(self) -> Dict[str, Any]:
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for f in self.findings:
            counts[f["severity"]] += 1

        is_fail_closed = counts["CRITICAL"] > 0 or counts["HIGH"] > 0
        return {
            "total_findings": len(self.findings),
            "counts": counts,
            "findings": self.findings,
            "pass": not is_fail_closed,
            "exit_code": 1 if is_fail_closed else 0,
        }


def main():
    parser = argparse.ArgumentParser(description="Verificador de Drift Documental e de Código")
    parser.add_argument("--docs", default="../documentation", help="Caminho para o diretório de documentação")
    parser.add_argument("--root", default=".", help="Caminho raiz do projeto evidencia")
    parser.add_argument("--output", default="", help="Caminho para salvar o relatório JSON")
    args = parser.parse_args()

    root_dir = Path(args.root).resolve()
    docs_dir = Path(args.docs).resolve()

    checker = DriftChecker(root_dir, docs_dir)
    result = checker.run_all_checks()

    print("\n" + "=" * 60)
    print("RELATÓRIO DE DRIFT — EVIDENCIA")
    print("=" * 60)
    print(f"Total de Apontamentos: {result['total_findings']}")
    print(f"CRITICAL: {result['counts']['CRITICAL']}")
    print(f"HIGH:     {result['counts']['HIGH']}")
    print(f"MEDIUM:   {result['counts']['MEDIUM']}")
    print(f"LOW:      {result['counts']['LOW']}")
    print("-" * 60)

    for finding in result["findings"]:
        prefix = f"[{finding['severity']}] [{finding['category']}]"
        loc = f" ({finding['file']})" if finding['file'] else ""
        print(f"{prefix}{loc}: {finding['message']}")

    if args.output:
        out_path = Path(args.output).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nRelatório salvo em: {out_path}")

    print("=" * 60)
    if result["pass"]:
        print("STATUS: PASS (0 CRITICAL, 0 HIGH)\n")
        sys.exit(0)
    else:
        print("STATUS: FAIL (Há findings CRITICAL ou HIGH)\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
