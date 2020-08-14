'''
Module of Android API for plyer.email.
'''

from f2email import Email
from jnius import autoclass, cast  # pylint: disable=no-name-in-module
from plyer.platforms.android import activity

Intent = autoclass('android.content.Intent')
AndroidString = autoclass('java.lang.String')


class AndroidEmail(Email):
    # pylint: disable=too-few-public-methods
    '''
    Implementation of Android email API.
    '''

    def _send(self, **kwargs):
        intent = Intent(Intent.ACTION_SEND)
        intent.setType('text/plain')

        recipient = kwargs.get('recipient')
        subject = kwargs.get('subject')
        text = kwargs.get('text')
        create_chooser = kwargs.get('create_chooser')
        attachment = kwargs.get('attachment')

        if recipient:
            intent.putExtra(Intent.EXTRA_EMAIL, ["fpflege@familien-altenpflege.de", recipient])
        if subject:
            android_subject = cast(
                'java.lang.CharSequence',
                AndroidString(subject)
            )
            intent.putExtra(Intent.EXTRA_SUBJECT, android_subject)
        if text:
            android_text = cast(
                'java.lang.CharSequence',
                AndroidString(text)
            )
            intent.putExtra(Intent.EXTRA_TEXT, android_text)
        if attachment:
            Fileprovider = autoclass("androidx.core.content.FileProvider")
            File = autoclass("java.io.File")
            app_context = activity.getApplication().getApplicationContext()
            uri = Fileprovider.getUriForFile(app_context, "org.fpflege.fileprovider", File(attachment))
            # print("uri", uri, uri.toString())  # content://org.fpflege.fileprovider/files/storage/emulated/0/fpflege/arbeitsblatt.M%C3%A4rz%202020.xlsx
            app_context.grantUriPermission("org.fpflege", uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
            parcelable = cast("android.os.Parcelable", uri)
            intent.putExtra(Intent.EXTRA_STREAM, parcelable)

        if create_chooser:
            chooser_title = cast(
                'java.lang.CharSequence',
                AndroidString('Send message with:')
            )
            activity.startActivity(
                Intent.createChooser(intent, chooser_title)
            )
        else:
            activity.startActivity(intent)


def instance():
    '''
    Instance for facade proxy.
    '''
    return AndroidEmail()
