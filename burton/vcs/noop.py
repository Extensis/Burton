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

    def add_file(self, file, xlf_repo_path = None):
        """Adds the file, or changes to the file, to the VCS"""

    def commit_changes(self, commit_message, xlf_repo_path = None):
        """Commits all changes with the specified commit message. Some VCSs,
        like Perforce and SVN, will automatically send these changes to the VCS
        server. Others, like Git, will need to upload their commits separately,
        which is done with the upload_changes method.
        """

    def upload_changes(self, xlf_repo_path = None):
        """Sends recent commits to the VCS server or origin. This is only
        required for VCSs, like Git, where uploading commits is done separately
        from committing. As such, it will get called every time commit_changes
        is called, but can be implemented as a no-op for VCSs which upload with
        their commits.
        """

    def revert_all(self, xlf_repo_path = None):
        """Reverts all files that have been checked out"""

    def revert(self, path, xlf_repo_path = None):
        """Reverts a file or directory at path. If the path is a directory,
        this method reverts that directory and all files under it recursively.
        This method will ignore files that have not been changed and are not
        marked for edit.
        """

    def revert_if_unchanged(self, path, xlf_repo_path = None):
        """Reverts all uchanged files under path. Uses the same logic as
        revert() when deciding which files to attempt to revert.
        """
