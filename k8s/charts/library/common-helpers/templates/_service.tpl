{{/* /k8s/charts/library/common-helpers/templates/_service.tpl */}}
{{/* vim: set filetype=mustache: */}}

{{/* --- Common Service Template --- */}}

{{/*
Defines a standard Service based on .Values.service settings.
It expects ports to be defined as a list under .Values.service.ports.
Each item in the list should have at least 'name' and 'port'.
'protocol' defaults to TCP, 'targetPort' defaults to 'port'.

Usage: {{ include "common-helpers.service" . }}
*/}}
{{- define "common-helpers.service" -}}
{{- if .Values.service }}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "common-helpers.fullname" . }}
  labels:
    {{- include "common-helpers.labels" . | nindent 4 }}
    {{- with .Values.service.labels }}
    {{- toYaml . | nindent 4 }}
    {{- end }}
  {{- with .Values.service.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  type: {{ .Values.service.type | default "ClusterIP" }}
  {{- if .Values.service.ports }}
  ports:
    {{- range .Values.service.ports }}
    {{- if not .name }}
      {{- fail (printf "%s: Each item in service.ports requires a 'name' field." (include "common-helpers.fullname" $)) }}
    {{- end }}
    {{- if not .port }}
      {{- fail (printf "%s: Each item in service.ports requires a 'port' field." (include "common-helpers.fullname" $)) }}
    {{- end }}
    - name: {{ .name }}
      port: {{ .port }}
      targetPort: {{ .targetPort | default .port }}
      {{- if .protocol }}
      protocol: {{ .protocol }}
      {{- end }}
      {{- /* Add NodePort logic only if service type needs it and value is provided */ -}}
      {{- if and (or (eq $.Values.service.type "NodePort") (eq $.Values.service.type "LoadBalancer")) .nodePort }}
      nodePort: {{ .nodePort }}
      {{- end }}
    {{- end }}
  {{- end }}
  selector:
    {{- include "common-helpers.selectorLabels" . | nindent 4 }}
    {{- /* Allow overriding/extending selector from values */ -}}
    {{- with .Values.service.selector }}
    {{- toYaml . | nindent 4 }}
    {{- end }}
  {{- /* Add other common Service spec fields if needed, driven by values */}}
  {{- if eq .Values.service.type "LoadBalancer" }}
  {{- with .Values.service.loadBalancerIP }}
  loadBalancerIP: {{ . }}
  {{- end }}
  {{- with .Values.service.loadBalancerSourceRanges }}
  loadBalancerSourceRanges:
    {{- toYaml . | nindent 4 }}
  {{- end }}
  {{- end }}
  {{- if eq .Values.service.type "ExternalName" }}
  {{- with .Values.service.externalName }}
  externalName: {{ . }}
  {{- end }}
  {{- end }}
  {{- /* Allow explicitly setting clusterIP, but use with caution */ -}}
  {{- with .Values.service.clusterIP }}
  clusterIP: {{ . }}
  {{- end }}
  {{- with .Values.service.externalIPs }}
  externalIPs:
    {{- toYaml . | nindent 4 }}
  {{- end }}
  {{- with .Values.service.sessionAffinity }}
  sessionAffinity: {{ . }}
  {{- end }}
  {{- with .Values.service.sessionAffinityConfig }}
  sessionAffinityConfig:
    {{- toYaml . | nindent 4 }}
  {{- end }}
{{- end }}{{/* .Values.service */}}
{{- end }}{{/* define "common-helpers.service" */}}

{{/* --- End Common Service Template --- */}}
