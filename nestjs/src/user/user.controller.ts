import { Controller, Body, Get, Inject, Injectable, Post,Header } from '@nestjs/common';
import { UserService } from './user.service';
import { UserEntity } from './user.entity';
import { InjectRepository } from '@nestjs/typeorm';

@Controller('/user')
export class UserController {

    constructor(private readonly userService: UserService) { }

    //   userService: UserService

    @Get('/list')
    findAll(): Promise<UserEntity[]> {
        return this.userService.findAll();
    }

    @Post()
    @Header('Access-Control-Allow-Origin', '*')
    async signin(@Body() body: any) {
        console.log(body.userID,body.password)
        return this.userService.createUser(body.userID, body.password);
    }
}

