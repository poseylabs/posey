{{/* /k8s/charts/library/common-helpers/templates/_pvc.tpl */}}
{{/* vim: set filetype=mustache: */}}

{{/* --- Common PVC Template --- */}}

{{/*
Defines a standard PersistentVolumeClaim based on .Values.persistence settings.
It checks if persistence is enabled before rendering.
It names the PVC using the convention "<fullname>-pvc".

Usage: {{ include "common-helpers.pvc" . }}
*/}}
{{- define "common-helpers.pvc" -}}
{{- if .Values.persistence.enabled }}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "common-helpers.fullname" . }}-pvc
  labels:
    {{- include "common-helpers.labels" . | nindent 4 }}
spec:
  accessModes:
    {{- range .Values.persistence.accessModes }}
    - {{ . | quote }}
    {{- end }}
  resources:
    requests:
      storage: {{ .Values.persistence.size | quote }}
  {{- /* Use storageClassName from values or omit if using default */ -}}
  {{- if .Values.persistence.storageClassName }}
  storageClassName: {{ .Values.persistence.storageClassName | quote }}
  {{- end }}
{{- end }}{{/* .Values.persistence.enabled */}}
{{- end }}{{/* define "common-helpers.pvc" */}}

{{/* --- End Common PVC Template --- */}} 