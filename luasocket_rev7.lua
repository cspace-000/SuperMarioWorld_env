--rev7 open close socket each step

local socket = require("socket.core")
local json = require("json")



defaultInput = {["P1 A"] = false, 
                ["P1 Up"] = false, 
                ["P1 Right"]=false, 
                ["P1 Left"]=false, 
                ["P1 Y"]=false, 
                ["P1 X"]=false,
                ["P1 Down"]=false, 
                ["P1 B"]=false}


function fromHost()
  --input from python.
  local recv  = sock:receive('*l')
  recv = json.decode(recv)
  return recv
end

function toHost(outputmessage)
  local endmsg = {'E'}
  local startmsg = {'S'}
  local sentmessage = {startmsg, outputmessage, endmsg}
  --print(sentmessage)
  local command = json.encode(sentmessage)
  

  sock:send(command)

end


function doAction(actcmd)

  local actioncommand = actcmd
  joypad.set(actioncommand)
  --emu.frameadvance()
end

function clearJoypad()
  controller = {}
  for b = 1,#defaultInput do
    controller["P1 " .. defaultInput[b]] = false
  end
  joypad.set(controller)
end
--gui.register(passiveUpdate) --undocumented. this function will call even if emulator paused

--getPositions()-----------------------------------------------------------------------
function marioX()
  
  local marioX = memory.read_s16_le(0x94)
  return marioX
end

function marioY()
  
  local marioY = memory.read_s16_le(0x96)
  return marioY
end

function screenX()
  marioX = memory.read_s16_le(0x94)
  local layer1x = memory.read_s16_le(0x1A);
  screenX = marioX-layer1x
  
  return screenX
end

function screenY()
  marioY = memory.read_s16_le(0x96)
  local layer1y = memory.read_s16_le(0x1C);
  screenY = marioY-layer1y
  
  return screenY
end
-----------------------------------------------------------------------------------------

--getSprites()----------------------------------------------------------------------------
function getPositions()
  if gameinfo.getromname() == "Super Mario World (USA)" then
    marioX = memory.read_s16_le(0x94)
    marioY = memory.read_s16_le(0x96)
    
    local layer1x = memory.read_s16_le(0x1A);
    local layer1y = memory.read_s16_le(0x1C);
    
    screenX = marioX-layer1x
    screenY = marioY-layer1y
  elseif gameinfo.getromname() == "Super Mario Bros." then
    marioX = memory.readbyte(0x6D) * 0x100 + memory.readbyte(0x86)
    marioY = memory.readbyte(0x03B8)+16
  
    screenX = memory.readbyte(0x03AD)
    screenY = memory.readbyte(0x03B8)
  end
end

function getTile(dx, dy)
  if gameinfo.getromname() == "Super Mario World (USA)" then
    x = math.floor((marioX+dx+8)/16)
    y = math.floor((marioY+dy)/16)
    
    return memory.readbyte(0x1C800 + math.floor(x/0x10)*0x1B0 + y*0x10 + x%0x10)
  elseif gameinfo.getromname() == "Super Mario Bros." then
    local x = marioX + dx + 8
    local y = marioY + dy - 16
    local page = math.floor(x/256)%2

    local subx = math.floor((x%256)/16)
    local suby = math.floor((y - 32)/16)
    local addr = 0x500 + page*13*16+suby*16+subx
    
    if suby >= 13 or suby < 0 then
      return 0
    end
    
    if memory.readbyte(addr) ~= 0 then
      return 1
    else
      return 0
    end
  end
end

function getSprites()
  if gameinfo.getromname() == "Super Mario World (USA)" then
    local sprites = {}
    for slot=0,11 do
      local status = memory.readbyte(0x14C8+slot)
      if status ~= 0 then
        spritex = memory.readbyte(0xE4+slot) + memory.readbyte(0x14E0+slot)*256
        spritey = memory.readbyte(0xD8+slot) + memory.readbyte(0x14D4+slot)*256
        sprites[#sprites+1] = {["x"]=spritex, ["y"]=spritey}
      end
    end   
    
    return sprites
  elseif gameinfo.getromname() == "Super Mario Bros." then
    local sprites = {}
    for slot=0,4 do
      local enemy = memory.readbyte(0xF+slot)
      if enemy ~= 0 then
        local ex = memory.readbyte(0x6E + slot)*0x100 + memory.readbyte(0x87+slot)
        local ey = memory.readbyte(0xCF + slot)+24
        sprites[#sprites+1] = {["x"]=ex,["y"]=ey}
      end
    end
    
    return sprites
  end
end

function getExtendedSprites()
  if gameinfo.getromname() == "Super Mario World (USA)" then
    local extended = {}
    for slot=0,11 do
      local number = memory.readbyte(0x170B+slot)
      if number ~= 0 then
        spritex = memory.readbyte(0x171F+slot) + memory.readbyte(0x1733+slot)*256
        spritey = memory.readbyte(0x1715+slot) + memory.readbyte(0x1729+slot)*256
        extended[#extended+1] = {["x"]=spritex, ["y"]=spritey}
      end
    end   
    
    return extended
  elseif gameinfo.getromname() == "Super Mario Bros." then
    return {}
  end
end

function getState()
  getPositions()
  
  sprites = getSprites()
  extended = getExtendedSprites()
  local BoxRadius = 6
  local inputs = {}
  
  for dy=-BoxRadius*16,BoxRadius*16,16 do
    for dx=-BoxRadius*16,BoxRadius*16,16 do
      inputs[#inputs+1] = 0
      
      tile = getTile(dx, dy)
      if tile == 1 and marioY+dy < 0x1B0 then
        inputs[#inputs] = 1
      end
      
      for i = 1,#sprites do
        distx = math.abs(sprites[i]["x"] - (marioX+dx))
        disty = math.abs(sprites[i]["y"] - (marioY+dy))
        if distx <= 8 and disty <= 8 then
          inputs[#inputs] = -1
        end
      end

      for i = 1,#extended do
        distx = math.abs(extended[i]["x"] - (marioX+dx))
        disty = math.abs(extended[i]["y"] - (marioY+dy))
        if distx < 8 and disty < 8 then
          inputs[#inputs] = -1
        end
      end
    end
  end
  
  --mariovx = memory.read_s8(0x7B)
  --mariovy = memory.read_s8(0x7D)
  --print(inputs)
  return inputs
end

n = 4
rec = 0
inGame = false
episode = 0
--level = 'levl1.State'
level = 'level2.State'
--level = 'level2.State'
TIMEOUTCONSTANT = 20
while true do
  --Reset Game
  if inGame == false then
    savestate.load(level)
    episode = episode + 1
    print('starting level :',episode)
    clearJoypad()
    currentFrame = 0
    rightmost = 0
    timeout = TIMEOUTCONSTANT
    inGame = true
    reward = 0
    v = 0
    d = 0
    c = 0
    death = false
    complete = false
    done = false
    action = defaultInput
    prev_position = memory.read_s16_le(0x94)
    emu.frameadvance()
  end
  --print(inGame)
    while inGame do
      if inGame == false then
        break
      end

      --print('current frame', currentFrame)
      --print(inGame)
      if currentFrame % n ==0 then

        sock = assert(socket.tcp())
        host, port = "127.0.0.1", 65432
        repeat 
        conn = sock:connect(host,port)
        until conn == 1

        action = fromHost()
        --print('recv' ,rec)
        rec = rec+1
        --print('action',action)
      end

      doAction(action)
      --print('action:', action)

      if currentFrame % n==0 then
        --print(state)
        --print('state')
        state = getState()
      end

      
      current_position = memory.read_s16_le(0x94)
      
      --Timeout
      if current_position > rightmost then --If Mario has moved past the furthest x_position in the last frame:
        rightmost = current_position --new position is the rightmost position
        timeout = TIMEOUTCONSTANT --reset timeout
      end


      --done = false
      timeout = timeout -1
      --print('timeout ',timeout)
      local timeoutBonus = current_position / 5


      --Mario is killed
      mario_alive = memory.read_s8(0x001496)
      if mario_alive > 40 then
        death = true
        done = true
      else 
        death = false
      end

      if rightmost > 4820 then --Completed the level 
        done = true
        complete = true
      end

      --Mario Timesout
      if timeout + timeoutBonus <=0 then --If mario times out
         -- If Mario died or hasn't progressed in the last 20 frames

          done = true
          death = true
      end
    
      
      --print(reward)
      
      --print(action)
      if currentFrame % n ==0 or done == true then



        velocity = memory.readbyte(0x7B)
        if velocity >= 200 then
          velocity = velocity -200
          velocity = velocity * -1
        end

        velocity = velocity / 50

        v = velocity


        if complete == true then
          c = 15
        end 
        if death == true then
          d = -15
        end
        
        reward = v + c + d


        if action['P1 A'] == true then
          act = 0
        elseif action['P1 Right'] == true then
          act = 1
        elseif action['P1 Left'] == true then
          act = 2
        elseif action['P1 B'] == true then
          act = 3    
        end

        r = reward / 15
        r = r * 1000
        r = math.floor(r)
        reward = r / 1000
        

        local srd = {state, reward, done, current_position, act}
 
        --score_int = math.floor(math.log10(current_position) + 1 + 0.5)
        toHost(srd)
        sock:close()

      end


      if done == true then
        --toHost(current_position)
        inGame = false
      end

      --get inputs from python
      --read gamestate
      --get death
      --get reward
    prev_position = current_position
    currentFrame = currentFrame+1
    emu.frameadvance()

    end
end

