class NoOp(object):
    """The NoOp class implements the VCS interface, with each method implemented
    as a no-op. This makes the NoOp class suitable for use when no VCS is being
    used, and as a default VCS class in the config file.

    In addition, the NoOp class may be used as a base class for other VCS
    classes, as a no-op is a reasonable default for all of the methods. However,
    VCS classes are not required to inherit from the NoOp class, as the VCS
    hierarchy uses duck typing.
    """

    def __init__(self):
        object.__init__(self)
        self.submodule_paths = []

    def add_submodule_path(self, submodule_path):
        self.submodule_paths.append(submodule_path)

    def update_path(self, path, submodule_path = None):
        """Updates the file or directory at path with the latest version from
        the VCS server or origin. If path is a directory, updates all files
        under that directory that are tracked by the VCS.
        """

    def add_file(self, file, submodule_path = None):
        """Adds the file to be tracked by the VCS, or does nothing if the file
        is already tracked by VCS. This is intended for new files that have
        never been tracked by the VCS. To mark changed files for inclusion into
        a commit, see mark_file_for_edit.
        """

    def mark_file_for_edit(self, file, submodule_path = None):
        """Marks a file as having changes that should be included in the next
        commit. Since some VCSs lock files up front, this method should be
        called on existing files before editing them.

        On some VCSs, like SVN, any changed file is included in a commit, so
        this method can be implemented as a no-op.
        """

    def commit_changes(self, commit_message):
        """Commits all changes with the specified commit message. Some VCSs,
        like Perforce and SVN, will automatically send these changes to the VCS
        server. Others, like Git, will need to upload their commits separately,
        which is done with the upload_changes method.
        """

    def upload_changes(self):
        """Sends recent commits to the VCS server or origin. This is only
        required for VCSs, like Git, where uploading commits is done separately
        from committing. As such, it will get called every time commit_changes
        is called, but can be implemented as a no-op for VCSs which upload with
        their commits.
        """

    def revert_all(self):
        """Reverts all files that have been checked out"""

    def revert(self, path, submodule_path = None):
        """Reverts a file or directory at path. If the path is a directory,
        this method reverts that directory and all files under it recursively.
        This method will ignore files that have not been changed and are not
        marked for edit.
        """

    def revert_if_unchanged(self, path, submodule_path = None):
        """Reverts all uchanged files under path. Uses the same logic as
        revert() when deciding which files to attempt to revert.
        """
