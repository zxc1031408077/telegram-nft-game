import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ContextTypes, ConversationHandler, MessageHandler, filters
)
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app import crud, schemas
from app.utils.helpers import get_settings

# 設置日誌
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# 對話狀態
SELECTING_GAME, SELECTING_ROOM, PLACING_BET, PLAYING_GAME = range(4)

class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
        self.active_games = {}  # 存儲活動遊戲狀態
    
    def setup_handlers(self):
        """設置處理器"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("menu", self.show_menu))
        self.application.add_handler(CommandHandler("shop", self.show_shop))
        self.application.add_handler(CommandHandler("nft", self.show_nft))
        self.application.add_handler(CommandHandler("balance", self.show_balance))
        
        # 遊戲選擇對話
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("play", self.play)],
            states={
                SELECTING_GAME: [CallbackQueryHandler(self.select_game)],
                SELECTING_ROOM: [CallbackQueryHandler(self.select_room)],
                PLACING_BET: [CallbackQueryHandler(self.place_bet)],
                PLAYING_GAME: [CallbackQueryHandler(self.play_game)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        self.application.add_handler(conv_handler)
        
        # 處理購買遊戲幣
        self.application.add_handler(MessageHandler(filters.Regex(r'^購買 \d+ 遊戲幣$'), self.handle_coin_purchase))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理 /start 命令"""
        user = update.effective_user
        db = SessionLocal()
        
        try:
            # 創建或獲取用戶
            db_user = crud.get_user_by_telegram_id(db, str(user.id))
            if not db_user:
                user_create = schemas.UserCreate(
                    telegram_id=str(user.id),
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    game_coin=0.0
                )
                db_user = crud.create_user(db, user_create)
                logger.info(f"New user created: {db_user.id}")
            
            await update.message.reply_text(
                f"歡迎 {user.first_name}！\n\n"
                f"你的遊戲幣餘額: {db_user.game_coin}\n\n"
                "使用 /menu 查看主選單\n"
                "使用 /play 開始遊戲\n"
                "使用 /shop 購買遊戲幣\n"
                "使用 /nft 查看你的NFT\n"
                "使用 /balance 查看餘額"
            )
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text("發生錯誤，請稍後再試。")
        finally:
            db.close()
    
    async def show_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """顯示主選單"""
        keyboard = [
            [InlineKeyboardButton("開始遊戲", callback_data="play")],
            [InlineKeyboardButton("購買遊戲幣", callback_data="shop")],
            [InlineKeyboardButton("我的NFT", callback_data="nft")],
            [InlineKeyboardButton("遊戲規則", callback_data="rules")],
            [InlineKeyboardButton("餘額查詢", callback_data="balance")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("請選擇操作:", reply_markup=reply_markup)
    
    async def show_shop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """顯示商店"""
        keyboard = [
            [InlineKeyboardButton("購買 10 遊戲幣 (10 USDT)", callback_data="buy_10")],
            [InlineKeyboardButton("購買 50 遊戲幣 (50 USDT)", callback_data="buy_50")],
            [InlineKeyboardButton("購買 100 遊戲幣 (100 USDT)", callback_data="buy_100")],
            [InlineKeyboardButton("返回主選單", callback_data="menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "遊戲幣商店:\n\n"
            "1 遊戲幣 = 1 USDT\n\n"
            "請選擇購買數量:",
            reply_markup=reply_markup
        )
    
    async def show_nft(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """顯示用戶的NFT"""
        user = update.effective_user
        db = SessionLocal()
        
        try:
            db_user = crud.get_user_by_telegram_id(db, str(user.id))
            if not db_user:
                await update.message.reply_text("請先使用 /start 命令註冊")
                return
            
            nfts = crud.get_nfts_by_owner(db, db_user.id)
            if not nfts:
                await update.message.reply_text("你還沒有任何NFT，快去遊戲中贏取吧！")
                return
            
            message = "你的NFT收藏:\n\n"
            for nft in nfts:
                message += f"• {nft.name} (ID: {nft.token_id})\n"
                if nft.description:
                    message += f"  {nft.description}\n"
                message += "\n"
            
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error showing NFTs: {e}")
            await update.message.reply_text("獲取NFT時發生錯誤")
        finally:
            db.close()
    
    async def show_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """顯示餘額"""
        user = update.effective_user
        db = SessionLocal()
        
        try:
            db_user = crud.get_user_by_telegram_id(db, str(user.id))
            if not db_user:
                await update.message.reply_text("請先使用 /start 命令註冊")
                return
            
            await update.message.reply_text(f"你的遊戲幣餘額: {db_user.game_coin}")
        except Exception as e:
            logger.error(f"Error showing balance: {e}")
            await update.message.reply_text("獲取餘額時發生錯誤")
        finally:
            db.close()
    
    async def play(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """開始遊戲流程"""
        keyboard = [
            [InlineKeyboardButton("踩地雷", callback_data="mines")],
            [InlineKeyboardButton("骰子大小", callback_data="dice")],
            [InlineKeyboardButton("21點", callback_data="blackjack")],
            [InlineKeyboardButton("射氣球", callback_data="balloons")],
            [InlineKeyboardButton("翻牌比大小", callback_data="cards")],
            [InlineKeyboardButton("返回主選單", callback_data="menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("請選擇遊戲類型:", reply_markup=reply_markup)
        return SELECTING_GAME
    
    async def select_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """選擇遊戲類型"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "menu":
            await query.edit_message_text("已返回主選單")
            return ConversationHandler.END
        
        game_type = query.data
        context.user_data["game_type"] = game_type
        
        db = SessionLocal()
        try:
            rooms = crud.get_available_rooms(db, game_type)
            
            if not rooms:
                await query.edit_message_text("目前沒有可用的房間，請稍後再試或創建新房間。")
                return ConversationHandler.END
            
            keyboard = []
            for room in rooms:
                keyboard.append([InlineKeyboardButton(
                    f"{room.name} ({room.current_players}/{room.max_players}) - 入場費: {room.entry_fee}",
                    callback_data=f"room_{room.id}"
                )])
            
            keyboard.append([InlineKeyboardButton("創建新房間", callback_data="create_room")])
            keyboard.append([InlineKeyboardButton("返回", callback_data="back")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text("請選擇房間:", reply_markup=reply_markup)
            return SELECTING_ROOM
        except Exception as e:
            logger.error(f"Error selecting game: {e}")
            await query.edit_message_text("發生錯誤，請稍後再試。")
            return ConversationHandler.END
        finally:
            db.close()
    
    async def select_room(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """選擇房間"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "back":
            await self.play(update, context)
            return SELECTING_GAME
        
        if query.data == "create_room":
            # 處理創建新房間邏輯
            await query.edit_message_text("創建新房間功能即將推出！")
            return ConversationHandler.END
        
        # 處理選擇現有房間
        room_id = int(query.data.split("_")[1])
        context.user_data["room_id"] = room_id
        
        # 這裡應該實現加入房間和下注邏輯
        await query.edit_message_text("請準備下注...")
        return PLACING_BET
    
    async def place_bet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """下注處理"""
        query = update.callback_query
        await query.answer()
        
        # 這裡實現下注邏輯
        await query.edit_message_text("遊戲開始!")
        return PLAYING_GAME
    
    async def play_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """遊戲進行中"""
        query = update.callback_query
        await query.answer()
        
        # 處理遊戲邏輯
        await query.edit_message_text("遊戲結束!")
        return ConversationHandler.END
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """取消對話"""
        await update.message.reply_text("操作已取消")
        return ConversationHandler.END
    
    async def handle_coin_purchase(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理遊戲幣購買"""
        text = update.message.text
        amount = int(text.split(" ")[1])  # 提取數量
        
        user_id = update.effective_user.id
        db = SessionLocal()
        
        try:
            user = crud.get_user_by_telegram_id(db, str(user_id))
            if user:
                # 這裡應該整合支付處理邏輯
                # 簡化版本直接增加遊戲幣
                new_balance = user.game_coin + amount
                crud.update_user_coins(db, user.id, new_balance)
                
                # 記錄交易
                transaction = schemas.TransactionCreate(
                    user_id=user.id,
                    amount=amount,
                    type="purchase",
                    description=f"Purchased {amount} coins"
                )
                crud.create_transaction(db, transaction)
                
                await update.message.reply_text(f"成功購買 {amount} 遊戲幣! 新餘額: {new_balance}")
            else:
                await update.message.reply_text("用戶不存在，請先使用 /start 命令")
        except Exception as e:
            logger.error(f"Error handling coin purchase: {e}")
            await update.message.reply_text("購買失敗，請稍後再試")
        finally:
            db.close()
    
    def run(self):
        """啟動機器人"""
        self.application.run_polling()
    
    def stop(self):
        """停止機器人"""
        self.application.stop()