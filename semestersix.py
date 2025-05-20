from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Dictionary to keep track of user states and semester data
user_states = {}
user_semester_data = {}

# Admin chat ID
ADMIN_CHAT_ID = 1119708892  # Replace with the actual admin chat ID

# Define the grade function
def grade(input_value: str, credit: float) -> float:
    grade_map = {
        's': 10.0,
        'a': 9.0,
        'b': 8.0,
        'c': 7.0,
        'd': 6.0,
        'e': 5.0,
        'f': 0.0,
        'o': 0.0
    }
    return grade_map.get(input_value.lower(), None) * credit if input_value.lower() in grade_map else None

# Define command handlers
async def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    await update.message.reply_text('Hi! This is EIE Assistant😎')

    # Notify admin
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f'User {user.full_name} (@{user.username}) started the bot.'
        )
        logger.info(f'Admin notification sent for user {user.full_name} (@{user.username})')
    except Exception as e:
        logger.error(f'Failed to send admin notification: {e}')

    keyboard = [
        [InlineKeyboardButton("EIE", callback_data='start_cgpa')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('SELECT YOUR DEPARTMENT : ', reply_markup=reply_markup)

async def help_command(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton( "EIE", callback_data='start_cgpa')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('STOPPED !!!\nENTER YOUR DEPARTMENT', reply_markup=reply_markup)

async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == 'start_cgpa':
        user_states[user_id] = 'awaiting_semester'
        keyboard = [
            [InlineKeyboardButton("Semester 1", callback_data='sem1'), InlineKeyboardButton("Semester 4", callback_data='sem4')],
            [InlineKeyboardButton("Semester 2", callback_data='sem2'), InlineKeyboardButton("Semester 5", callback_data='sem5')],
            [InlineKeyboardButton("Semester 3", callback_data='sem3'), InlineKeyboardButton("Semester 6", callback_data='sem6')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('Please select the semester:', reply_markup=reply_markup)

    elif data.startswith('sem'):
        user_semester_data[user_id] = {'semester': data}
        await process_semester_selection(query, user_id, data)

    elif user_states.get(user_id, '').startswith('sem'):
        await process_grade_selection(query, user_id, data)

async def process_semester_selection(query, user_id, semester):
    subjects = {
        'sem1': ['M1', 'BEE', 'CP', 'EG', 'BEE LAB', 'CP LAB'],
        'sem2': ['M2', 'PHYSICS', 'CHEMISTRY', 'ENGLISH', 'WORKSHOP', 'PHYSICS LAB', 'CHEMISTRY LAB'],
        'sem3': ['M3', 'CT', 'EDF', 'EC', 'DLTD', 'BIOLOGY', 'EC LAB', 'EDF LAB', 'HM'],
        'sem4': ['LIC', 'SS', 'TMS', 'EEI', 'DSOOP', 'LIC LAB', 'TMS LAB', 'DSOOP LAB', 'HM'],
        'sem5': ['II', 'MA', 'CS', 'EP', 'VLSI', 'ISD LAB', 'VLSI LAB', 'MA LAB', 'OEC', 'HM'],
        'sem6': ['PC', 'ESD', 'RAA', 'DSP', 'IEM', 'PC LAB', 'VI LAB', 'ESD LAB', 'OEC', 'HM']
    }
    subjects = subjects[semester]
    user_states[user_id] = f'{semester}_{subjects[0].lower()}'
    await query.edit_message_text(f'Enter your {subjects[0]} grade:', reply_markup=grade_buttons(subjects[0]))

async def process_grade_selection(query, user_id, grade_value):
    current_state = user_states.get(user_id)
    semester, subject = current_state.split('_')
    credit_map = {
        'M1': 4.0, 'BEE': 4.0, 'CP': 3.0, 'EG': 3.0, 'BEE LAB': 1.5, 'CP LAB': 1.5,
        'M2': 4.0, 'PHYSICS': 4.0, 'CHEMISTRY': 4.0, 'ENGLISH': 3.0, 'WORKSHOP': 1.5, 'PHYSICS LAB': 1.5, 'CHEMISTRY LAB': 1.5,
        'M3': 4.0, 'CT': 4.0, 'EDF': 4.0, 'EC': 3.0, 'DLTD': 3.0, 'BIOLOGY': 2.0, 'EC LAB': 1.5, 'EDF LAB': 1.0, 'HM': 4.0,
        'LIC': 3.0, 'SS': 3.0, 'TMS': 3.0, 'EEI': 3.0, 'DSOOP': 3.0, 'LIC LAB': 1.5, 'TMS LAB': 1.5, 'DSOOP LAB': 1.5, 'HM': 4.0,
        'II': 4.0, 'MA': 3.0, 'CS': 4.0, 'EP': 2.0, 'VLSI': 3.0, 'ISD LAB': 1.5, 'VLSI LAB': 1.5, 'MA LAB': 1.5, 'OEC': 3.0, 'HM': 4.0,
        'PC': 4, 'ESD': 4, 'RAA': 3, 'IEM': 3, 'DSP': 3, 'PC LAB': 1.5, 'VI LAB': 1.5, 'ESD LAB': 1.5, 'OEC': 3.0, 'HM': 4.0
    }
    credit = credit_map.get(subject.upper(), 0.0)
    grade_val = grade(grade_value, credit)

    if grade_val is not None:
        user_semester_data[user_id][subject.upper()] = grade_val
        subjects = {
            'sem1': ['M1', 'BEE', 'CP', 'EG', 'BEE LAB', 'CP LAB'],
            'sem2': ['M2', 'PHYSICS', 'CHEMISTRY', 'ENGLISH', 'WORKSHOP', 'PHYSICS LAB', 'CHEMISTRY LAB'],
            'sem3': ['M3', 'CT', 'EDF', 'EC', 'DLTD', 'BIOLOGY', 'EC LAB', 'EDF LAB', 'HM'],
            'sem4': ['LIC', 'SS', 'TMS', 'EEI', 'DSOOP', 'LIC LAB', 'TMS LAB', 'DSOOP LAB', 'HM'],
            'sem5': ['II', 'MA', 'CS', 'EP', 'VLSI', 'ISD LAB', 'VLSI LAB', 'MA LAB', 'OEC', 'HM'],
            'sem6':['PC', 'ESD', 'RAA', 'IEM', 'DSP', 'PC LAB', 'VI LAB', 'ESD LAB', 'OEC', 'HM']

        }[semester]

        next_subject_idx = subjects.index(subject.upper()) + 1
        if next_subject_idx < len(subjects):
            next_subject = subjects[next_subject_idx]
            user_states[user_id] = f'{semester}_{next_subject.lower()}'
            await query.edit_message_text(f'Enter your {next_subject} grade:', reply_markup=grade_buttons(next_subject))
        else:
            await calculate_cgpa(query, user_id, semester)
    else:
        await query.edit_message_text(f'Invalid grade. Please enter a valid grade for {subject.upper()} (s, a, b, c, d, e, f).', reply_markup=grade_buttons(subject.upper()))

def grade_buttons(subject):
    keyboard = [
        [InlineKeyboardButton("S", callback_data='s'),InlineKeyboardButton("C", callback_data='c')],
        [InlineKeyboardButton("A", callback_data='a'),InlineKeyboardButton("D", callback_data='d')],
        [InlineKeyboardButton("B", callback_data='b'),InlineKeyboardButton("E", callback_data='e')],
        [InlineKeyboardButton("Not taken", callback_data='o'),InlineKeyboardButton("F", callback_data='f')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def calculate_cgpa(query, user_id, semester) -> None:
    data = user_semester_data[user_id]
    total_credits = 0
    total_points = 0

    # Calculate total credits and total points based on the selected semester
    if semester == 'sem1':
        total_credits = sum([4.0, 4.0, 3.0, 3.0, 1.5, 1.5])
        total_points = sum(data.get(subject, 0.0) for subject in ['M1', 'BEE', 'CP', 'EG', 'BEE LAB', 'CP LAB'])
    elif semester == 'sem2':
        total_credits = sum([4.0, 4.0, 4.0, 3.0, 1.5, 1.5, 1.5])
        total_points = sum(data.get(subject, 0.0) for subject in ['M2', 'PHYSICS', 'CHEMISTRY', 'ENGLISH', 'WORKSHOP', 'PHYSICS LAB', 'CHEMISTRY LAB'])
    elif semester == 'sem3':
        if 'HM' in data and data['HM'] == 0.0:
            total_credits = sum([4.0, 4.0, 4.0, 3.0, 3.0, 2.0, 1.5, 1.0])
            total_points = sum(data.get(subject, 0.0) for subject in ['M3', 'CT', 'EDF', 'EC', 'DLTD', 'BIOLOGY', 'EC LAB', 'EDF LAB'])
        else:
            total_credits = sum([4.0, 4.0, 4.0, 3.0, 3.0, 2.0, 1.5, 1.0, 4.0])
            total_points = sum(data.get(subject, 0.0) for subject in ['M3', 'CT', 'EDF', 'EC', 'DLTD', 'BIOLOGY', 'EC LAB', 'EDF LAB', 'HM'])
    elif semester == 'sem4':
        if 'HM' in data and data['HM'] == 0.0:
            total_credits = sum([3.0, 3.0, 3.0, 3.0, 3.0, 1.5, 1.5, 1.5])
            total_points = sum(data.get(subject, 0.0) for subject in ['LIC', 'SS', 'TMS', 'EEI', 'DSOOP', 'LIC LAB', 'TMS LAB', 'DSOOP LAB'])
        else:
            total_credits = sum([3.0, 3.0, 3.0, 3.0, 3.0, 1.5, 1.5, 1.5, 4.0])
            total_points = sum(data.get(subject, 0.0) for subject in ['LIC', 'SS', 'TMS', 'EEI', 'DSOOP', 'LIC LAB', 'TMS LAB', 'DSOOP LAB', 'HM'])
    elif semester == 'sem5':
        if 'HM' in data and data['HM'] == 0.0:
            total_credits = sum([4.0, 3.0, 4.0, 2.0, 3.0, 1.5, 1.5, 1.5, 3.0])
            total_points = sum(data.get(subject, 0.0) for subject in ['II', 'MA', 'CS', 'EP', 'VLSI', 'ISD LAB', 'VLSI LAB', 'MA LAB', 'OEC'])
        else:
            total_credits = sum([4.0, 3.0, 4.0, 2.0, 3.0, 1.5, 1.5, 1.5, 3.0, 4.0])
            total_points = sum(data.get(subject, 0.0) for subject in ['II', 'MA', 'CS', 'EP', 'VLSI', 'ISD LAB', 'VLSI LAB', 'MA LAB', 'OEC', 'HM'])
    elif semester == 'sem6':
        if 'HM' in data and data['HM'] == 0.0:
            total_credits = sum([4.0, 4.0, 3.0, 3.0, 3.0, 1.5, 1.5, 1.5, 3.0])
            total_points = sum(data.get(subject, 0.0) for subject in ['PC', 'ESD', 'RAA', 'DSP', 'IEM', 'PC LAB', 'VI LAB', 'ESD LAB', 'OEC'])
        else:
            total_credits = sum([4.0, 4.0, 3.0, 3.0, 3.0, 1.5, 1.5, 1.5, 3.0, 4.0])
            total_points = sum(data.get(subject, 0.0) for subject in ['PC', 'ESD', 'RAA', 'DSP', 'IEM', 'PC LAB', 'VI LAB', 'ESD LAB', 'OEC', 'HM'])

    # Calculate CGPA if valid total credits are available
    if total_credits > 0:
        cgpa = total_points / total_credits
        await query.edit_message_text(f'Your {semester} CGPA is...{cgpa:.2f}')

        # Reset user state and data after calculation
        user_states.pop(user_id, None)
        user_semester_data.pop(user_id, None)

        # Provide option to start CGPA calculation again
        keyboard = [
            [InlineKeyboardButton("Semester 1", callback_data='sem1'), InlineKeyboardButton("Semester 4", callback_data='sem4')],
            [InlineKeyboardButton("Semester 2", callback_data='sem2'), InlineKeyboardButton("Semester 5", callback_data='sem5')],
            [InlineKeyboardButton("Semester 3", callback_data='sem3'), InlineKeyboardButton("Semester 6", callback_data='sem6')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text('Please select the semester:', reply_markup=reply_markup)
    else:
        await query.edit_message_text('No valid grades entered to calculate CGPA.')

async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    text = update.message.text

    if text.lower() == 'cgpa':
        user_states[user_id] = 'awaiting_semester'
        keyboard = [
            [InlineKeyboardButton("Semester 1", callback_data='sem1'), InlineKeyboardButton("Semester 4", callback_data='sem4')],
            [InlineKeyboardButton("Semester 2", callback_data='sem2'), InlineKeyboardButton("Semester 5", callback_data='sem5')],
            [InlineKeyboardButton("Semester 3", callback_data='sem3'), InlineKeyboardButton("Semester 6", callback_data='sem6')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Please select the semester:', reply_markup=reply_markup)
    else:
        await update.message.reply_text( " I can't get you.Please type /start")

def main() -> None:
    application = Application.builder().token("6674039941:AAEdCBuegYdZwWrgM1fPHeSfudYSEWkfJzY").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()
