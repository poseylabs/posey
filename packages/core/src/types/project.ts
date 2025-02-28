export enum ProjectStatus {
  ACTIVE = 'active',
  ARCHIVED = 'archived',
  DELETED = 'deleted',
  NEW = 'new'
}

export interface Project {
  id: string;
  name: string;
  status: ProjectStatus;
}
