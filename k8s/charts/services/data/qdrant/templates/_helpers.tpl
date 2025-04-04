{{/* This file can be removed if not defining any chart-specific helpers */}}

{{/*
Return the appropriate apiVersion for statefulset.
*/}}
{{- define "qdrant.statefulset.apiVersion" -}}
{{- if semverCompare ">=1.9-0" .Capabilities.KubeVersion.GitVersion -}}
{{- print "apps/v1" -}}
{{- else -}}
{{- print "apps/v1beta2" -}}
{{- end -}}
{{- end -}} 