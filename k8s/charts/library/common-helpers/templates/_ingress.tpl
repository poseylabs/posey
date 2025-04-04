{{/*
Define a common Ingress template.
Minimum required values:
  EITHER .Values.ingress.hostname OR .Values.ingress.subdomain

Optional overrides/settings:
  .Values.ingress.enabled (defaults to true if hostname/subdomain is set, otherwise false. Set explicitly to false to disable.)
  .Values.ingress.baseDomain (defaults to db.posey.ai)
  .Values.ingress.className (defaults to nginx)
  .Values.ingress.annotations (merged with defaults)
  .Values.ingress.paths (defaults to path: /, pathType: ImplementationSpecific)
  .Values.ingress.tls.enabled (defaults to true if ingress enabled. Set explicitly to false to disable TLS.)
  .Values.ingress.tls.secretName (defaults to generated name like <hostname-as-kebab-case>-tls)
  .Values.ingress.forceSSL (defaults to true, adds redirect annotation if TLS is enabled)
  .Values.service.ingressPortName (defaults to http)
*/}}
{{- define "common-helpers.ingress" -}}

{{- /* --- Configuration Variables --- */}}
{{- $fullName := include "common-helpers.fullname" . -}}

{{- /* --- Determine Hostname --- */}}
{{- $hostname := "" -}}
{{- if .Values.ingress.hostname -}}
{{-   $hostname = .Values.ingress.hostname -}}
{{- else if .Values.ingress.subdomain -}}
{{-   $baseDomain := .Values.ingress.baseDomain | default "db.posey.ai" -}}
{{-   $hostname = printf "%s.%s" .Values.ingress.subdomain $baseDomain -}}
{{- end -}}

{{- /* --- Determine if Ingress should be enabled --- */}}
{{- /* Default to true if hostname/subdomain is set, unless explicitly disabled */}}
{{- $explicitlyEnabledSet := hasKey .Values.ingress "enabled" -}}
{{- $ingressEnabled := false -}}
{{- if $explicitlyEnabledSet -}}
{{-   $ingressEnabled = .Values.ingress.enabled -}}
{{- else if $hostname -}}
{{-   $ingressEnabled = true -}} {{/* Infer enabled=true if hostname/subdomain present */}}
{{- end -}}

{{- /* --- Set Defaults (only if enabled) --- */}}
{{- $className := .Values.ingress.className | default "nginx" -}}
{{- $defaultPaths := list (dict "path" "/" "pathType" "ImplementationSpecific") -}}
{{- $paths := .Values.ingress.paths | default $defaultPaths -}}

{{- /* --- Annotation Logic --- */}}
{{- $defaultAnnotations := dict "cert-manager.io/cluster-issuer" "letsencrypt-prod" -}}
{{- $finalAnnotations := $defaultAnnotations -}}

{{- /* --- TLS and Force SSL Logic --- */}}
{{- /* Check if TLS section exists and if .enabled is explicitly false */}}
{{- $tlsExplicitlyDisabled := false -}}
{{- if .Values.ingress.tls -}}
{{-   if hasKey .Values.ingress.tls "enabled" -}}
{{-     $tlsExplicitlyDisabled = eq .Values.ingress.tls.enabled false -}}
{{-   end -}}
{{- end -}}
{{- $tlsEnabled := and $ingressEnabled $hostname (not $tlsExplicitlyDisabled) -}}

{{- /* Add force SSL redirect annotation if TLS is enabled and forceSSL is not explicitly false */}}
{{- $forceSSLEnabled := and $tlsEnabled (ne (.Values.ingress.forceSSL | default true) false) -}}
{{- if $forceSSLEnabled -}}
{{-   $_ := set $finalAnnotations "nginx.ingress.kubernetes.io/force-ssl-redirect" "true" -}}
{{- end -}}
{{- /* Merge user annotations over defaults */}}
{{- $finalAnnotations = mergeOverwrite $finalAnnotations (.Values.ingress.annotations | default dict) -}}

{{- /* --- Determine TLS Secret Name --- */}}
{{- $generatedSecretName := printf "%s-tls" ($hostname | replace "." "-") -}}
{{- $tlsSecretName := $generatedSecretName -}} {{/* Default to generated */}}
{{- if .Values.ingress.tls -}}
{{-   $tlsSecretName = .Values.ingress.tls.secretName | default $generatedSecretName -}}
{{- end -}}

{{- /* --- Render Ingress --- */}}
{{- if and $ingressEnabled $hostname $paths -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ $fullName }}
  labels:
    {{- include "common-helpers.labels" . | nindent 4 }}
  {{- with $finalAnnotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  {{- if $className }}
  ingressClassName: {{ $className }}
  {{- end }}
  {{- if $tlsEnabled }}
  tls:
    - hosts:
        # Use the determined hostname
        - {{ $hostname | quote }}
      # Use the determined or provided secret name
      secretName: {{ $tlsSecretName }}
  {{- end }}
  rules:
    # Use the determined hostname
    - host: {{ $hostname | quote }}
      http:
        paths:
          # Use the determined or provided paths
          {{- range $paths }}
          - path: {{ .path }}
            pathType: {{ .pathType }}
            backend:
              service:
                name: {{ $fullName }}
                port:
                  # Use specified ingress port name, default to 'http'
                  name: {{ $.Values.service.ingressPortName | default "http" }}
          {{- end }}
{{- end }}
{{- end -}} 