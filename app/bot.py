import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .game import game_manager
from .models import User, GameRoom
from .config import Config

# 設置日誌
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("play", self.play))
        self.application.add_handler(CommandHandler("balance", self.balance))
        self.application.add_handler(CommandHandler("create_room", self.create_room))
        self.application.add_handler(CommandHandler("join", self.join_room))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """發送歡迎消息"""
        user = update.effective_user
        await update.message.reply_html(
            rf"嗨 {user.mention_html()}！歡迎來到 NFT 遊戲世界！",
            reply_markup=self.main_menu_keyboard()
        )
        
        # 保存用戶到數據庫
        async with AsyncSession(self.application.db_engine) as session:
            result = await session.execute(select(User).where(User.telegram_id == user.id))
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                new_user = User(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
                session.add(new_user)
                await session.commit()
    
    async def play(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """顯示遊戲選擇菜單"""
        keyboard = [
            [InlineKeyboardButton("骰子大小", callback_data="game_dice")],
            [InlineKeyboardButton("踩地雷", callback_data="game_mines")],
            [InlineKeyboardButton("21點", callback_data="game_blackjack")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("請選擇遊戲類型：", reply_markup=reply_markup)
    
    async def balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查詢餘額"""
        user = update.effective_user
        async with AsyncSession(self.application.db_engine) as session:
            result = await session.execute(select(User).where(User.telegram_id == user.id))
            db_user = result.scalar_one_or_none()
            
            if db_user:
                await update.message.reply_text(f"您的餘額: {db_user.balance} 遊戲幣")
            else:
                await update.message.reply_text("請先使用 /start 註冊")
    
    async def create_room(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """創建遊戲房間"""
        user = update.effective_user
        bet_amount = 10.0  # 默认下注金额
        
        # 檢查餘額
        async with AsyncSession(self.application.db_engine) as session:
            result = await session.execute(select(User).where(User.telegram_id == user.id))
            db_user = result.scalar_one_or_none()
            
            if not db_user or db_user.balance < bet_amount:
                await update.message.reply_text("餘額不足，無法創建房間")
                return
            
            # 扣除下注金額
            db_user.balance -= bet_amount
            await session.commit()
        
        # 創建房間
        room_id = f"room_{user.id}_{hash(str(user.id) + str(update.message.date))}"
        game_manager.create_room(room_id, user.id, "dice", bet_amount)
        
        # 保存房間到數據庫
        async with AsyncSession(self.application.db_engine) as session:
            new_room = GameRoom(
                room_id=room_id,
                game_type="dice",
                creator_id=user.id,
                players=str([user.id]),
                bet_amount=bet_amount,
                status="waiting"
            )
            session.add(new_room)
            await session.commit()
        
        join_link = f"https://t.me/{context.bot.username}?start=join_{room_id}"
        await update.message.reply_text(
            f"房間已創建！房間號: {room_id}\n"
            f"下注金額: {bet_amount}遊戲幣\n"
            f"邀請鏈接: {join_link}\n"
            f"等待其他玩家加入...\n"
            f"輸入 /start_room_{room_id} 開始遊戲"
        )
    
    async def join_room(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """加入遊戲房間"""
        user = update.effective_user
        
        if not context.args:
            await update.message.reply_text("請提供房間號，例如: /join room_123")
            return
        
        room_id = context.args[0]
        
        # 檢查房間是否存在
        if room_id not in game_manager.active_rooms:
            await update.message.reply_text("房間不存在或已開始遊戲")
            return
        
        # 檢查餘額
        bet_amount = game_manager.active_rooms[room_id]["bet_amount"]
        async with AsyncSession(self.application.db_engine) as session:
            result = await session.execute(select(User).where(User.telegram_id == user.id))
            db_user = result.scalar_one_or_none()
            
            if not db_user or db_user.balance < bet_amount:
                await update.message.reply_text("餘額不足，無法加入房間")
                return
            
            # 扣除下注金額
            db_user.balance -= bet_amount
            await session.commit()
        
        # 加入房間
        if game_manager.join_room(room_id, user.id):
            # 更新數據庫中的房間信息
            async with AsyncSession(self.application.db_engine) as session:
                result = await session.execute(select(GameRoom).where(GameRoom.room_id == room_id))
                db_room = result.scalar_one_or_none()
                
                if db_room:
                    players = eval(db_room.players)
                    if user.id not in players:
                        players.append(user.id)
                        db_room.players = str(players)
                        await session.commit()
            
            await update.message.reply_text(f"已加入房間 {room_id}")
        else:
            await update.message.reply_text("加入房間失敗")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理按鈕回調"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("game_"):
            game_type = query.data.split("_")[1]
            await query.edit_message_text(text=f"已選擇: {game_type}遊戲")
    
    def main_menu_keyboard(self):
        """主菜單鍵盤"""
        keyboard = [
            [InlineKeyboardButton("開始遊戲", callback_data="play")],
            [InlineKeyboardButton("我的餘額", callback_data="balance")],
            [InlineKeyboardButton("創建房間", callback_data="create_room")],
        ]
        return InlineKeyboardMarkup(keyboard)