{{/* This file can be removed if not defining any chart-specific helpers */}}

{{/*
Return the appropriate apiVersion for statefulset.
This is kept locally as it's specific to the kind of resource (StatefulSet)
*/}}
{{- define "couchbase.statefulset.apiVersion" -}}
{{- if semverCompare ">=1.9-0" .Capabilities.KubeVersion.GitVersion -}}
{{- print "apps/v1" -}}
{{- else -}}
{{- print "apps/v1beta2" -}}
{{- end -}}
{{- end -}} 