{{/* /k8s/charts/library/common-helpers/templates/_serviceaccount.tpl */}}
{{/* vim: set filetype=mustache: */}}

{{/* --- Common ServiceAccount Template --- */}}

{{/*
Defines a standard ServiceAccount based on .Values.serviceAccount settings.
It uses the common-helpers.serviceAccountName helper to determine the name.

Usage: {{ include "common-helpers.serviceaccount" . }}
*/}}
{{- define "common-helpers.serviceaccount" -}}
{{- if .Values.serviceAccount.create -}}
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "common-helpers.serviceAccountName" . }}
  labels:
    {{- include "common-helpers.labels" . | nindent 4 }}
  {{- with .Values.serviceAccount.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
automountServiceAccountToken: {{ .Values.serviceAccount.automount }}
{{- end }}
{{- end -}}

{{/* --- End Common ServiceAccount Template --- */}} 